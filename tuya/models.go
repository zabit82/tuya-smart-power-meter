package tuya

// TokenResponse is the response from GET /v1.0/token
type TokenResponse struct {
	Result struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
		UID          string `json:"uid"`
		ExpireTime   int    `json:"expire_time"`
	} `json:"result"`
	Success bool   `json:"success"`
	T       int64  `json:"t"`
	Msg     string `json:"msg"`
}

// DeviceListResponse is the response from GET /v1.0/iot-03/devices
type DeviceListResponse struct {
	Result struct {
		List  []Device `json:"list"`
		Total int      `json:"total"`
	} `json:"result"`
	Success bool   `json:"success"`
	Msg     string `json:"msg"`
}

// Device holds basic device information
type Device struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Online      bool   `json:"online"`
	Category    string `json:"category"`
	ProductName string `json:"product_name"`
	ProductID   string `json:"product_id"`
	UID         string `json:"uid"`
	ActiveTime  int64  `json:"active_time"`
	UpdateTime  int64  `json:"update_time"`
}

// ShadowPropertiesResponse is the response from GET /v2.0/cloud/thing/{id}/shadow/properties
type ShadowPropertiesResponse struct {
	Result struct {
		Properties []ShadowProperty `json:"properties"`
	} `json:"result"`
	Success bool   `json:"success"`
	Msg     string `json:"msg"`
}

// ShadowProperty is a single data point from the shadow properties endpoint
type ShadowProperty struct {
	Code       string      `json:"code"`
	CustomName string      `json:"custom_name"`
	DpID       int         `json:"dp_id"`
	Time       int64       `json:"time"`
	Type       string      `json:"type"`
	Value      interface{} `json:"value"`
}

// ModelResponse is the response from GET /v2.0/cloud/thing/{id}/model
type ModelResponse struct {
	Result struct {
		Model string `json:"model"` // embedded JSON string
	} `json:"result"`
	Success bool   `json:"success"`
	Msg     string `json:"msg"`
}

// ModelSpec is the parsed structure of the model JSON
type ModelSpec struct {
	ModelID  string         `json:"modelId"`
	Services []ModelService `json:"services"`
}

// ModelService is a group of model properties
type ModelService struct {
	Properties []ModelProperty `json:"properties"`
}

// ModelProperty stores spec info for a single property code
type ModelProperty struct {
	Code     string   `json:"code"`
	Name     string   `json:"name"`
	TypeSpec TypeSpec `json:"typeSpec"`
}

// TypeSpec defines the data type, scale, unit etc. for a property
type TypeSpec struct {
	Type  string  `json:"type"`
	Scale float64 `json:"scale"`
	Unit  string  `json:"unit"`
	Max   float64 `json:"max"`
	Min   float64 `json:"min"`
	Step  float64 `json:"step"`
}

// PropertySpec is a flattened lookup map entry for a code
type PropertySpec struct {
	Name  string
	Scale float64
	Unit  string
	Type  string
}
