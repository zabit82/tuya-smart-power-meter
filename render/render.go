package render

import (
	"fmt"
	"math"
	"os"
	"strings"
	"time"

	"power-meter-tuya/tuya"

	"github.com/olekukonko/tablewriter"
)

// DevicesTable prints a summary table of all devices
func DevicesTable(devices []tuya.Device) {
	fmt.Println("\n📋  DEVICES")
	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"Name", "ID", "Online", "Category", "Product Name", "Last Update"})
	table.SetBorder(true)
	table.SetHeaderColor(
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
	)
	table.SetColumnColor(
		tablewriter.Colors{tablewriter.FgWhiteColor},
		tablewriter.Colors{tablewriter.FgYellowColor},
		tablewriter.Colors{},
		tablewriter.Colors{tablewriter.FgMagentaColor},
		tablewriter.Colors{tablewriter.FgGreenColor},
		tablewriter.Colors{tablewriter.FgHiBlackColor},
	)

	for _, d := range devices {
		online := "✅ yes"
		if !d.Online {
			online = "❌ no"
		}
		updateTime := time.Unix(d.UpdateTime, 0).Format("2006-01-02 15:04:05")
		if d.UpdateTime == 0 {
			updateTime = "-"
		}
		table.Append([]string{
			d.Name,
			d.ID,
			online,
			d.Category,
			d.ProductName,
			updateTime,
		})
	}
	table.Render()
}

// ShadowTable prints the shadow properties of a device with scaled values and units
func ShadowTable(deviceName string, props []tuya.ShadowProperty, specs map[string]tuya.PropertySpec) {
	header := fmt.Sprintf("\n⚡  STATUS — %s", strings.ToUpper(deviceName))
	fmt.Println(header)

	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"Code", "Name", "Value", "Unit", "Type", "Last Update"})
	table.SetBorder(true)
	table.SetHeaderColor(
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.Bold, tablewriter.FgCyanColor},
	)
	table.SetColumnColor(
		tablewriter.Colors{tablewriter.FgYellowColor},
		tablewriter.Colors{tablewriter.FgWhiteColor},
		tablewriter.Colors{tablewriter.FgGreenColor, tablewriter.Bold},
		tablewriter.Colors{tablewriter.FgCyanColor},
		tablewriter.Colors{tablewriter.FgHiBlackColor},
		tablewriter.Colors{tablewriter.FgHiBlackColor},
	)

	for _, p := range props {
		spec := specs[p.Code]
		name := spec.Name
		if name == "" {
			name = p.Code
		}
		unit := spec.Unit
		typeStr := p.Type
		if typeStr == "" {
			typeStr = spec.Type
		}

		valueStr := formatValue(p.Value, spec.Scale, typeStr)
		ts := "-"
		if p.Time > 0 {
			// Time comes in milliseconds
			t := p.Time
			if t > 1e12 {
				t /= 1000
			}
			ts = time.Unix(t, 0).Format("01-02 15:04:05")
		}

		table.Append([]string{p.Code, name, valueStr, unit, typeStr, ts})
	}
	table.Render()
}

// formatValue applies scale to numeric values and formats nicely
func formatValue(v interface{}, scale float64, typeStr string) string {
	switch val := v.(type) {
	case float64:
		if scale > 0 && typeStr == "value" {
			divisor := math.Pow(10, scale)
			result := val / divisor
			// Determine decimal places from scale
			decimals := int(scale)
			return fmt.Sprintf("%.*f", decimals, result)
		}
		if val == math.Trunc(val) {
			return fmt.Sprintf("%.0f", val)
		}
		return fmt.Sprintf("%g", val)
	case bool:
		if val {
			return "true"
		}
		return "false"
	default:
		return fmt.Sprintf("%v", v)
	}
}
