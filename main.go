package main

import (
	"fmt"
	"log"
	"os"
	"strings"

	"power-meter-tuya/render"
	"power-meter-tuya/tuya"
)

func main() {
	clientID := os.Getenv("TUYA_CLIENT_ID")
	clientSecret := os.Getenv("TUYA_CLIENT_SECRET")
	deviceIDsEnv := os.Getenv("TUYA_DEVICE_IDS")
	apiHost := os.Getenv("TUYA_API_HOST")

	if clientID == "" || clientSecret == "" {
		log.Fatal("TUYA_CLIENT_ID and TUYA_CLIENT_SECRET must be set")
	}
	if apiHost == "" {
		apiHost = "https://openapi.tuyaeu.com"
	}

	fmt.Printf("🔌  Connecting to %s...\n", apiHost)

	client := tuya.NewClient(clientID, clientSecret, apiHost)

	fmt.Println("🔑  Obtaining access token...")
	if err := client.GetToken(); err != nil {
		log.Fatalf("Authentication failed: %v", err)
	}
	fmt.Println("✅  Authenticated successfully.")

	// Determine which devices to query
	var deviceIDs []string
	if deviceIDsEnv != "" {
		for _, id := range strings.Split(deviceIDsEnv, ",") {
			id = strings.TrimSpace(id)
			if id != "" {
				deviceIDs = append(deviceIDs, id)
			}
		}
	}

	var devices []tuya.Device

	if len(deviceIDs) > 0 {
		fmt.Printf("\n🔍  Fetching %d device(s)...\n", len(deviceIDs))
		for _, id := range deviceIDs {
			d, err := client.GetDevice(id)
			if err != nil {
				fmt.Printf("  ⚠️  Could not fetch device %s: %v\n", id, err)
				continue
			}
			devices = append(devices, *d)
		}
	} else {
		fmt.Println("\n🔍  Fetching all devices from project...")
		var err error
		devices, err = client.GetDevices()
		if err != nil {
			log.Fatalf("Failed to list devices: %v", err)
		}
		fmt.Printf("   Found %d device(s).\n", len(devices))
	}

	if len(devices) == 0 {
		fmt.Println("\n⚠️  No devices found. Make sure devices are linked to your cloud project.")
		os.Exit(0)
	}

	// Print devices summary table
	render.DevicesTable(devices)

	// Fetch and print status for each device
	fmt.Println("\n📡  Fetching device statuses...")
	for _, device := range devices {
		// Fetch model specs for scale/unit info (non-fatal if unavailable)
		specs, err := client.GetPropertySpecs(device.ID)
		if err != nil {
			fmt.Printf("  ⚠️  Could not get property specs for %s: %v\n", device.Name, err)
			specs = map[string]tuya.PropertySpec{}
		}

		// Use shadow properties endpoint (works for power meters and most devices)
		props, err := client.GetShadowProperties(device.ID)
		if err != nil {
			fmt.Printf("  ⚠️  Could not get status for %s (%s): %v\n", device.Name, device.ID, err)
			continue
		}

		render.ShadowTable(device.Name, props, specs)
	}

	fmt.Println("\n✅  Done.")
}
