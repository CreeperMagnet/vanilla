#####################################################################################
# Proper setup
#####################################################################################

# Importing all the various libraries I need... a lot.
import urllib.request, json, os, shutil, zipfile, re

# The link to Mojang's version manifest. This probably shouldn't change.
manifest_url = 'http://launchermeta.mojang.com/mc/game/version_manifest.json'

# A storage string to log all the files
list = []

#####################################################################################
# Set up data from mojang's servers to read in other parts of the program
#####################################################################################

def json_from_url(url) :
    return json.loads(urllib.request.urlopen(url).read())

version_manifest = json_from_url(manifest_url)
latest_version_data = json_from_url(version_manifest['versions'][0]['url'])
objects = json_from_url(latest_version_data['assetIndex']['url'])['objects']

#####################################################################################
# Defining the get_jar functionality
#####################################################################################

def get_jar(name) :
    url = latest_version_data['downloads'][name]['url']
    path = os.path.abspath(os.path.join("..","data_extractor",name+".jar"))
    os.makedirs(os.path.dirname(path), exist_ok = True)
    urllib.request.urlretrieve(url,path)
    return path

#####################################################################################
# Extracting assets and data from client jar
#####################################################################################

client_jar = get_jar('client')
with zipfile.ZipFile(client_jar) as archive :
    for object in archive.namelist() :
        if not (object.endswith(('.class','.xml','.jfc')) or object.startswith("META-INF") or "/".join(object.split("/")[1:]) in objects) :
            list.append(os.path.normpath(object))
            path = os.path.abspath(os.path.join('..',object))
            if object.endswith('.json') and os.path.exists(path) :
                with archive.open(object) as f1 :
                    json1 = json.loads(f1.read().decode("utf-8"))
                    with open(path, encoding="utf8") as f2 :
                        json2 = json.load(f2)
                    if json.dumps(json1, sort_keys=True) == json.dumps(json2, sort_keys=True) :
                        continue
            os.makedirs(os.path.dirname(path),exist_ok=True)
            archive.extract(object, os.path.abspath(os.path.join('..')))

#####################################################################################
# Extracting reports and worldgen from server jar and converting them into snbt
#####################################################################################

server_jar = get_jar('server')
os.makedirs('server_jar',exist_ok = True)
os.chdir('server_jar')
os.system("java -DbundlerMainClass=net.minecraft.data.Main -jar "+ server_jar +" --reports --output data")
for root, directories, files in os.walk('data') :
    for file in files :
        # Make an array from the path so I can tell what it starts with
        path_array = os.path.normpath(os.path.join(root,file)).split(os.path.sep)
        # Ignore anything that isn't the reports
        if path_array[1] == "reports" :
            if path_array[2] == "worldgen" :
                del path_array[1:3]
            else :
                path_array = path_array[1:]
            joined_path_array = os.path.sep.join(path_array)
            if not file.endswith('.nbt') :
                list.append(joined_path_array)
            source_path = os.path.join(root,file)
            path = os.path.abspath(os.path.join('..','..',joined_path_array))
            if file.endswith('.json') and os.path.exists(path) :
                with open(source_path, encoding="utf8") as f1 :
                    json1 = json.load(f1)
                    with open(path, encoding="utf8") as f2 :
                        json2 = json.load(f2)
                    if json.dumps(json1, sort_keys=True) == json.dumps(json2, sort_keys=True) :
                        continue
            os.makedirs(os.path.dirname(path),exist_ok=True)
            shutil.copyfile(source_path,path)


decode_path = os.path.abspath(os.path.join('..','..'))
os.system('java -DbundlerMainClass=net.minecraft.data.Main -jar '+ server_jar + ' --dev --input '+decode_path+' --output snbt')
for root, directories, files in os.walk('snbt') :
    for file in files :
        if file.endswith('.snbt') :
            # Make an array from the path so I can tell what it starts with
            path_array = os.path.normpath(os.path.join(root,file)).split(os.path.sep)
            # Ignore anything that isn't the reports
            nbt_path_array = path_array[1:]
            path_array = path_array[1:]
            nbt_path_array[-1] = nbt_path_array[-1].replace('.snbt','.nbt')
            joined_nbt_path_array = os.path.sep.join(nbt_path_array)
            joined_path_array = os.path.sep.join(path_array)
            list.append(joined_path_array)
            source_path = os.path.join(root,file)
            final_path =os.path.abspath(os.path.join('..','..',joined_path_array))
            shutil.move(source_path,final_path)
            a_file = open(final_path, "r")
            lines = a_file.readlines()
            a_file.close()
            new_file = open(final_path, "w")
            for line in lines:
                if not re.search('\\s+DataVersion:.+',line.lstrip("\n")) :
                    new_file.write(line)
            new_file.close()


#####################################################################################
# Clean-up from the last couple steps (client/server jar extraction, nbt -> snbt -> json)
#####################################################################################

os.chdir('..')

try : shutil.rmtree('server_jar')
except: pass

os.remove('server.jar')
os.remove('client.jar')

#####################################################################################
# Extracting cached data from resource links using index off the internet
#####################################################################################

for object in objects :
    list.append(os.path.normpath(os.path.join('assets',object)))
    if not object.startswith('icons/') :
        hash = objects[object]['hash']
        destination_path = os.path.abspath(os.path.join("..","","assets",object))
        os.makedirs(os.path.dirname(destination_path),exist_ok=True)
        try :
            size = os.path.getsize(destination_path)
            if size == objects[object]['size'] :
                continue
        except : pass
        object_url = "https://resources.download.minecraft.net/"+hash[:2]+"/"+hash
        print("Downloading: assets/"+object)
        urllib.request.urlretrieve(object_url, destination_path)

#####################################################################################
# Removing any files that aren't supposed to be in the assets/data
#####################################################################################

core_path = os.path.abspath(os.path.join('..'))
for folder in ['assets','data','reports'] :
    for root, directories, files in os.walk(os.path.join(core_path,folder)) :
        for file in files :
            final_path = os.path.join(root,file)[len(os.path.join(core_path)):].lstrip('\\')
            if final_path not in list:
                print("File removed:",final_path)
                os.remove(os.path.abspath(os.path.join(core_path,final_path)))
