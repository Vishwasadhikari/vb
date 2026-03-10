-- Get the Players service to manage player data
local Players = game:GetService("Players")

-- Get the coin object (script should be inside the coin part)
local coin = script.Parent

local function onTouch(hit)
    if not hit.Parent or not hit.Parent:FindFirstChild("Humanoid") then
        return
    end

    local player = Players:GetPlayerFromCharacter(hit.Parent)
    if not player then
        return
    end

    -- Get or create leaderstats
    local leaderstats = player:FindFirstChild("leaderstats")
    if not leaderstats then
        leaderstats = Instance.new("Folder")
        leaderstats.Name = "leaderstats"
        leaderstats.Parent = player
    end

    -- Get or create Points (must be in scope for the rest of the function)
    local points = leaderstats:FindFirstChild("Points")
    if not points then
        points = Instance.new("IntValue")
        points.Name = "Points"
        points.Value = 0
        points.Parent = leaderstats
    end

    -- Award points and remove the coin
    points.Value = points.Value + 10
    coin:Destroy()
end

coin.Touched:Connect(onTouch)
