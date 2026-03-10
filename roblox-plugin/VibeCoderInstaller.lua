-- VibeCoder Installer Plugin (paste into a Studio Plugin script)
-- Usage:
-- 1) In the web app, generate code.
-- 2) Click "Copy Plugin Bundle".
-- 3) In Roblox Studio, open this plugin, paste JSON, click "Build".

local HttpService = game:GetService("HttpService")
local StudioService = game:GetService("StudioService")

local PLUGIN_TITLE = "VibeCoder Installer"
local BUNDLE_TYPE = "vibecoder_plugin_bundle_v1"

local toolbar = plugin:CreateToolbar("VibeCoder")
local button = toolbar:CreateButton("Installer", "Open VibeCoder Installer", "rbxassetid://4458901886")
button.ClickableWhenViewportHidden = true

local widgetInfo = DockWidgetPluginGuiInfo.new(
	Enum.InitialDockState.Right,
	false,
	false,
	420,
	520,
	340,
	420
)

local widget = plugin:CreateDockWidgetPluginGui("VibeCoderInstallerWidget", widgetInfo)
widget.Title = PLUGIN_TITLE

local root = Instance.new("Frame")
root.BackgroundColor3 = Color3.fromRGB(20, 23, 33)
root.BorderSizePixel = 0
root.Size = UDim2.fromScale(1, 1)
root.Parent = widget

local header = Instance.new("TextLabel")
header.BackgroundTransparency = 1
header.Size = UDim2.new(1, -24, 0, 24)
header.Position = UDim2.new(0, 12, 0, 10)
header.Font = Enum.Font.GothamBold
header.TextSize = 16
header.TextColor3 = Color3.fromRGB(229, 231, 235)
header.TextXAlignment = Enum.TextXAlignment.Left
header.Text = "Paste Plugin Bundle JSON"
header.Parent = root

local hint = Instance.new("TextLabel")
hint.BackgroundTransparency = 1
hint.Size = UDim2.new(1, -24, 0, 34)
hint.Position = UDim2.new(0, 12, 0, 36)
hint.Font = Enum.Font.Gotham
hint.TextSize = 12
hint.TextColor3 = Color3.fromRGB(148, 163, 184)
hint.TextXAlignment = Enum.TextXAlignment.Left
hint.TextYAlignment = Enum.TextYAlignment.Top
hint.TextWrapped = true
hint.Text = "In the web app: Generate → Copy Plugin Bundle. Paste here and click Build. This will create Scripts in the right services."
hint.Parent = root

local box = Instance.new("TextBox")
box.ClearTextOnFocus = false
box.MultiLine = true
box.TextXAlignment = Enum.TextXAlignment.Left
box.TextYAlignment = Enum.TextYAlignment.Top
box.Font = Enum.Font.Code
box.TextSize = 12
box.TextColor3 = Color3.fromRGB(229, 231, 235)
box.BackgroundColor3 = Color3.fromRGB(15, 23, 42)
box.BorderSizePixel = 0
box.Size = UDim2.new(1, -24, 1, -150)
box.Position = UDim2.new(0, 12, 0, 76)
box.Text = ""
box.Parent = root

local boxCorner = Instance.new("UICorner")
boxCorner.CornerRadius = UDim.new(0, 10)
boxCorner.Parent = box

local status = Instance.new("TextLabel")
status.BackgroundTransparency = 1
status.Size = UDim2.new(1, -24, 0, 40)
status.Position = UDim2.new(0, 12, 1, -68)
status.Font = Enum.Font.Gotham
status.TextSize = 12
status.TextColor3 = Color3.fromRGB(148, 163, 184)
status.TextXAlignment = Enum.TextXAlignment.Left
status.TextYAlignment = Enum.TextYAlignment.Top
status.TextWrapped = true
status.Text = "Ready."
status.Parent = root

local buttonRow = Instance.new("Frame")
buttonRow.BackgroundTransparency = 1
buttonRow.Size = UDim2.new(1, -24, 0, 38)
buttonRow.Position = UDim2.new(0, 12, 1, -38)
buttonRow.Parent = root

local buildBtn = Instance.new("TextButton")
buildBtn.Size = UDim2.new(0, 120, 1, 0)
buildBtn.Position = UDim2.new(0, 0, 0, 0)
buildBtn.Font = Enum.Font.GothamBold
buildBtn.TextSize = 14
buildBtn.TextColor3 = Color3.fromRGB(34, 211, 238)
buildBtn.BackgroundColor3 = Color3.fromRGB(24, 48, 62)
buildBtn.BorderSizePixel = 0
buildBtn.Text = "Build"
buildBtn.Parent = buttonRow

local clearBtn = Instance.new("TextButton")
clearBtn.Size = UDim2.new(0, 120, 1, 0)
clearBtn.Position = UDim2.new(0, 130, 0, 0)
clearBtn.Font = Enum.Font.GothamBold
clearBtn.TextSize = 14
clearBtn.TextColor3 = Color3.fromRGB(148, 163, 184)
clearBtn.BackgroundColor3 = Color3.fromRGB(30, 41, 59)
clearBtn.BorderSizePixel = 0
clearBtn.Text = "Clear"
clearBtn.Parent = buttonRow

local corners1 = Instance.new("UICorner")
corners1.CornerRadius = UDim.new(0, 10)
corners1.Parent = buildBtn
local corners2 = Instance.new("UICorner")
corners2.CornerRadius = UDim.new(0, 10)
corners2.Parent = clearBtn

local function getServiceRoot(serviceName: string)
	if serviceName == "Workspace" then
		return workspace
	end
	local ok, svc = pcall(function()
		return game:GetService(serviceName)
	end)
	if ok and svc then
		return svc
	end
	return nil
end

local function ensureFolder(parent: Instance, name: string)
	local existing = parent:FindFirstChild(name)
	if existing and existing:IsA("Folder") then
		return existing
	end
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = parent
	return folder
end

local function splitPath(path: string)
	local parts = {}
	for part in string.gmatch(path, "[^/]+") do
		table.insert(parts, part)
	end
	return parts
end

local function installScript(entry)
	local path = tostring(entry.path or "")
	local className = tostring(entry.className or "Script")
	local source = tostring(entry.source or "")
	if path == "" or source == "" then
		return false, "Missing path/source"
	end

	local parts = splitPath(path)
	local rootName = parts[1]
	local rootInst = getServiceRoot(rootName)
	if not rootInst then
		return false, "Unknown root: " .. rootName
	end

	-- Build folders for intermediate segments
	local parent = rootInst
	for i = 2, #parts - 1 do
		parent = ensureFolder(parent, parts[i])
	end

	local scriptName = parts[#parts] or "VibeCoderScript"
	local scriptObj = Instance.new(className == "LocalScript" and "LocalScript" or "Script")
	scriptObj.Name = scriptName
	scriptObj.Source = source
	scriptObj.Parent = parent

	return true, path
end

local function decodeBundle(text: string)
	local ok, decoded = pcall(function()
		return HttpService:JSONDecode(text)
	end)
	if not ok then
		return nil, "Invalid JSON"
	end
	if type(decoded) ~= "table" or decoded.type ~= BUNDLE_TYPE then
		return nil, "Not a VibeCoder bundle"
	end
	if type(decoded.scripts) ~= "table" then
		return nil, "Bundle missing scripts"
	end
	return decoded, nil
end

buildBtn.MouseButton1Click:Connect(function()
	local text = box.Text or ""
	if text:gsub("%s+", "") == "" then
		status.Text = "Paste the bundle JSON first."
		return
	end

	local bundle, err = decodeBundle(text)
	if not bundle then
		status.Text = "Error: " .. tostring(err)
		return
	end

	local created = 0
	local failures = {}
	plugin:Activate(true)

	local okHistory = pcall(function()
		StudioService:RecordUndo("VibeCoder Build", function()
			for _, s in ipairs(bundle.scripts) do
				local okInstall, msg = installScript(s)
				if okInstall then
					created += 1
				else
					table.insert(failures, tostring(msg))
				end
			end
		end)
	end)

	if not okHistory then
		-- Fallback without undo wrapper (older Studio)
		for _, s in ipairs(bundle.scripts) do
			local okInstall, msg = installScript(s)
			if okInstall then
				created += 1
			else
				table.insert(failures, tostring(msg))
			end
		end
	end

	if #failures > 0 then
		status.Text = string.format("Created %d script(s). Some failed: %s", created, table.concat(failures, "; "))
	else
		status.Text = string.format("Created %d script(s). Done!", created)
	end
end)

clearBtn.MouseButton1Click:Connect(function()
	box.Text = ""
	status.Text = "Cleared."
end)

button.Click:Connect(function()
	widget.Enabled = not widget.Enabled
end)

