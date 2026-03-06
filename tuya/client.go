package tuya

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sort"
	"strings"
	"time"
)

// emptyBodySHA256 is the SHA256 hash of an empty string, used for GET requests
const emptyBodySHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

// Client is a Tuya OpenAPI client
type Client struct {
	clientID     string
	clientSecret string
	host         string
	accessToken  string
	httpClient   *http.Client
}

// NewClient creates a new Tuya API client
func NewClient(clientID, clientSecret, host string) *Client {
	return &Client{
		clientID:     clientID,
		clientSecret: clientSecret,
		host:         strings.TrimRight(host, "/"),
		httpClient:   &http.Client{Timeout: 15 * time.Second},
	}
}

func nowMs() string { return fmt.Sprintf("%d", time.Now().UnixMilli()) }

func hmacSHA256(secret, payload string) string {
	h := hmac.New(sha256.New, []byte(secret))
	h.Write([]byte(payload))
	return strings.ToUpper(hex.EncodeToString(h.Sum(nil)))
}

func sha256hex(s string) string {
	h := sha256.New()
	h.Write([]byte(s))
	return hex.EncodeToString(h.Sum(nil))
}

// buildStringToSign builds the canonical string per Tuya v2 signature spec
func buildStringToSign(method, body string, headers map[string]string, urlPath string) string {
	bodyHash := emptyBodySHA256
	if body != "" {
		bodyHash = sha256hex(body)
	}

	var headerStr string
	if len(headers) > 0 {
		keys := make([]string, 0, len(headers))
		for k := range headers {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		parts := make([]string, 0, len(keys))
		for _, k := range keys {
			parts = append(parts, k+":"+headers[k])
		}
		headerStr = strings.Join(parts, "\n")
	}

	return strings.Join([]string{
		strings.ToUpper(method),
		bodyHash,
		headerStr,
		urlPath,
	}, "\n")
}

// GetToken fetches a new access token using grant_type=1
func (c *Client) GetToken() error {
	t := nowMs()
	urlPath := "/v1.0/token?grant_type=1"
	sts := buildStringToSign("GET", "", nil, urlPath)
	payload := c.clientID + t + sts
	sig := hmacSHA256(c.clientSecret, payload)

	url := fmt.Sprintf("%s%s", c.host, urlPath)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("creating token request: %w", err)
	}

	req.Header.Set("client_id", c.clientID)
	req.Header.Set("t", t)
	req.Header.Set("sign", sig)
	req.Header.Set("sign_method", "HMAC-SHA256")
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("executing token request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("reading token response: %w", err)
	}

	var tokenResp TokenResponse
	if err := json.Unmarshal(body, &tokenResp); err != nil {
		return fmt.Errorf("parsing token response: %w\nbody: %s", err, string(body))
	}

	if !tokenResp.Success {
		return fmt.Errorf("token request failed: %s (body: %s)", tokenResp.Msg, string(body))
	}

	c.accessToken = tokenResp.Result.AccessToken
	return nil
}

// get performs an authenticated GET request and returns the raw body
func (c *Client) get(urlPath string) ([]byte, error) {
	if c.accessToken == "" {
		return nil, fmt.Errorf("no access token; call GetToken() first")
	}

	t := nowMs()
	sts := buildStringToSign("GET", "", nil, urlPath)
	payload := c.clientID + c.accessToken + t + sts
	sig := hmacSHA256(c.clientSecret, payload)

	url := fmt.Sprintf("%s%s", c.host, urlPath)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	req.Header.Set("client_id", c.clientID)
	req.Header.Set("access_token", c.accessToken)
	req.Header.Set("t", t)
	req.Header.Set("sign", sig)
	req.Header.Set("sign_method", "HMAC-SHA256")
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("executing request: %w", err)
	}
	defer resp.Body.Close()

	return io.ReadAll(resp.Body)
}

// GetDevices returns all devices in the cloud project (paginated)
func (c *Client) GetDevices() ([]Device, error) {
	var allDevices []Device
	page := 1
	pageSize := 20

	for {
		urlPath := fmt.Sprintf("/v1.0/iot-03/devices?page_no=%d&page_size=%d", page, pageSize)
		body, err := c.get(urlPath)
		if err != nil {
			return nil, fmt.Errorf("fetching devices page %d: %w", page, err)
		}

		var resp DeviceListResponse
		if err := json.Unmarshal(body, &resp); err != nil {
			return nil, fmt.Errorf("parsing device list: %w\nbody: %s", err, string(body))
		}

		if !resp.Success {
			return nil, fmt.Errorf("device list request failed: %s (body: %s)", resp.Msg, string(body))
		}

		allDevices = append(allDevices, resp.Result.List...)

		if len(allDevices) >= resp.Result.Total || len(resp.Result.List) < pageSize {
			break
		}
		page++
	}

	return allDevices, nil
}

// GetDevice returns info about a single device
func (c *Client) GetDevice(deviceID string) (*Device, error) {
	urlPath := fmt.Sprintf("/v1.0/devices/%s", deviceID)
	body, err := c.get(urlPath)
	if err != nil {
		return nil, fmt.Errorf("fetching device %s: %w", deviceID, err)
	}

	var resp struct {
		Result  Device `json:"result"`
		Success bool   `json:"success"`
		Msg     string `json:"msg"`
	}
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("parsing device info: %w\nbody: %s", err, string(body))
	}

	if !resp.Success {
		return nil, fmt.Errorf("device info request failed: %s (body: %s)", resp.Msg, string(body))
	}

	return &resp.Result, nil
}

// GetShadowProperties returns live properties from the shadow endpoint
// (works for devices where /v1.0/devices/{id}/status returns 'function not support')
func (c *Client) GetShadowProperties(deviceID string) ([]ShadowProperty, error) {
	urlPath := fmt.Sprintf("/v2.0/cloud/thing/%s/shadow/properties", deviceID)
	body, err := c.get(urlPath)
	if err != nil {
		return nil, fmt.Errorf("fetching shadow properties for %s: %w", deviceID, err)
	}

	var resp ShadowPropertiesResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("parsing shadow properties: %w\nbody: %s", err, string(body))
	}

	if !resp.Success {
		return nil, fmt.Errorf("shadow properties failed: %s (body: %s)", resp.Msg, string(body))
	}

	return resp.Result.Properties, nil
}

// GetPropertySpecs returns the model specification for a device (code → spec lookup)
func (c *Client) GetPropertySpecs(deviceID string) (map[string]PropertySpec, error) {
	urlPath := fmt.Sprintf("/v2.0/cloud/thing/%s/model", deviceID)
	body, err := c.get(urlPath)
	if err != nil {
		return nil, fmt.Errorf("fetching model for %s: %w", deviceID, err)
	}

	var resp ModelResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("parsing model response: %w\nbody: %s", err, string(body))
	}

	if !resp.Success {
		// Non-fatal: model may not be available; return empty map
		return map[string]PropertySpec{}, nil
	}

	var spec ModelSpec
	if err := json.Unmarshal([]byte(resp.Result.Model), &spec); err != nil {
		// Non-fatal
		return map[string]PropertySpec{}, nil
	}

	result := make(map[string]PropertySpec)
	for _, svc := range spec.Services {
		for _, prop := range svc.Properties {
			result[prop.Code] = PropertySpec{
				Name:  prop.Name,
				Scale: prop.TypeSpec.Scale,
				Unit:  prop.TypeSpec.Unit,
				Type:  prop.TypeSpec.Type,
			}
		}
	}
	return result, nil
}
