-- @description import obj pbr project 
-- @author      Issa
-- @version     0.1
-- @shortcut    alt+0


-- initialize available path 
env = { 
    "G:\\Scanned_Forest_Woods\\ScansBox\\" 
    }

inPath= "C:\\"
for p = 1, #env do
    chek = octane.file.exists(env[p])
    if chek == true then
        inPath = env[p]
    end
end



-- file browzer prop
dialogProperties =
    {
        browseDirectory = true,
        type  = 2,
        title = "Load OBJ with map in folder",
        save  = false,
        wildcards = "*.png;*.jpg;*.obj",
        path = inPath
    }

path = octane.gui.showDialog(dialogProperties)
print(path.result)

list = octane.file.listDirectory(path.result, true, false, true, false)

-- nil nodes init
geonode = {}; matnode = {}; texnode = {}; placenode = {}
imgExt = {".png", ".jpg" }
maps = {"alb","dif","norm","hei","roug"} -- "cavi"
bakeSizerList = {}


imgSizeTab = { type = octane.NT_IMAGE_RESOLUTION, name = octane.file.getFileName(list[1]), position = {-400, -200}  }
imgSize = octane.node.create(imgSizeTab)
imgSize:setAttribute(octane.A_VALUE, {512*2, 512*2, 0})

root = octane.project.getSceneGraph()
geo = root:findNodes(1, true)
hmove = #geo

function findType( name, liste )
    -- get name if in list
    for p = 1, #liste do
        if string.find(name:lower(), liste[p]) ~= nil then
            return liste[p]
        end
    end
    return ".non"
end

function texSize( nam, pose )
    -- return texture baker node
    tab = {      
            type = octane.NT_TEX_BAKED_IMAGE,
            name = nam,
            position = pose
        }

    nodeTexSize = octane.node.create(tab)
    nodeTexSize:setPinValue(octane.P_RGB_BAKING, true)

    return nodeTexSize
end


-- node creations loop
for p = 1, #list do
    ex  = octane.file.getFileExtension(list[p])
    nam = octane.file.getFileName(list[p])
    
    if ex == ".obj" then
        tab = {      
            type = octane.NT_GEO_MESH,
            name = nam,
            position = {0+hmove*400, 100}
        }

        geonode = octane.node.create(tab)
        geonode:setAttribute(octane.A_FILENAME, list[p], true)

        --placement
        placetab = {      
            type = octane.NT_GEO_PLACEMENT,
            name = nam,
            position = {0+hmove*400, 200}
        }
        
        matrix = octane.matrix.makeRotX(-1.5708)

        placenode = octane.node.create(placetab)
        placenode:setPinValue(octane.P_TRANSFORM, matrix, true)

        --Material
        mattab = {      
            type = octane.NT_MAT_UNIVERSAL,
            name = nam,
            position = {0+hmove*400, 0}
        }
        
        matnode = octane.node.create(mattab)

    end
    
    textype = findType(nam, maps)
    extype = findType(ex, imgExt)  

    

    if (extype ~= ".non") and (bakeSizerList[textype] == nil) and  (textype ~= '.non') then  
        print("For ", nam, "==>", textype, extype ) 

        texnode = octane.node.create({      
            type = octane.NT_TEX_IMAGE,
            name = nam,
            position = {-p*80+180+hmove*400, -100}
        })

        -- call func
        texsizer = texSize( "<> "..nam, {-p*80+180+hmove*400, -100+50} )

        texnode:setAttribute(octane.A_FILENAME, list[p], true)
        texsizer:connectToIx(1, texnode)
        texsizer:connectToIx(3, imgSize )

        bakeSizerList[textype] = texsizer
        
    end
end



-- nodes connections
if not (type(geonode) == "tabe") then
    
    placenode:connectToIx(2, geonode)
    geonode:connectToIx(1, matnode)
    
    --{"alb","dif","norm","hei","roug","cavi"}
    print("XX")


    if bakeSizerList.alb ~= nil then
        print(bakeSizerList.alb)
        matnode:connectToIx(2, bakeSizerList.alb)
    end

    if bakeSizerList.dif ~= nil then
        print(bakeSizerList.dif)
        matnode:connectToIx(2, bakeSizerList.dif)
    end

    if bakeSizerList.norm ~= nil then
        print(bakeSizerList.norm)
        matnode:connectToIx(28, bakeSizerList.norm)
    end

    if bakeSizerList.hei ~= nil then
        print(bakeSizerList.hei)
        
        dispnode = octane.node.create({      
            type = octane.NT_DISPLACEMENT,
            name = bakeSizerList.hei.name,
            position = {150*2+hmove*400, -100}
        })

        --set disp val
        dispnode:setPinValue(octane.P_BLACK_LEVEL, 0.5)
        dispnode:setPinValue(octane.P_AMOUNT, 0.2)

        bakeSizerList.hei.position = {150*2+hmove*400, -150}
        imgSize.position = {hmove*400, -150}
        matnode:connectToIx(29, dispnode)
        dispnode:connectToIx(1, bakeSizerList.hei)
    end

    if bakeSizerList.roug ~= nil then
        print(bakeSizerList.roug)
        matnode:connectToIx(6, bakeSizerList.roug)
    end


end