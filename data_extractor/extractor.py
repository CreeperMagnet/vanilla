#####################################################################################
# Proper setup
#####################################################################################

# Importing all the various libraries I need... a lot.
import urllib.request, json, os, shutil, zipfile

# The files to be extracted from the client jar.
files_extracted_from_jar = ['assets','data']

# The link to Mojang's version manifest. This probably shouldn't change.
manifest_url = 'http://launchermeta.mojang.com/mc/game/version_manifest.json'

# A storage string to be written to a .txt later
list = []
size_list = []

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
            size_list.append(archive.getinfo(object).file_size)
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
# Extracting reports and worldgen from server jar
#####################################################################################

server_jar = get_jar('server')
os.makedirs('server_jar',exist_ok = True)
os.chdir('server_jar')
os.system("java -DbundlerMainClass=net.minecraft.data.Main -jar "+ server_jar +" --reports --output data")
try: shutil.rmtree(os.path.abspath(os.path.join('..','..','data','minecraft','worldgen')))
except: pass
try: shutil.rmtree(os.path.abspath(os.path.join('..','..','reports')))
except: pass
shutil.move(os.path.abspath(os.path.join('data','reports','worldgen','minecraft')),os.path.abspath(os.path.join('..','..','data','minecraft','worldgen')))
shutil.move(os.path.abspath(os.path.join('data','reports')),os.path.abspath(os.path.join('..','..','reports')))

#decode_path = os.path.abspath(os.path.join('..','..','data','minecraft','structures'))
#os.system('java -DbundlerMainClass=net.minecraft.data.Main -jar '+ server_jar + ' --dev --input '+decode_path+' --output '+decode_path)

os.chdir('..')
try: shutil.rmtree(os.path.abspath(os.path.join('server_jar')))
except: pass

os.remove('server.jar')
os.remove('client.jar')

#####################################################################################
# Extracting cached data from resource links using index off the internet
#####################################################################################

for object in objects :
    list.append(os.path.normpath(os.path.join('assets',object)))
    size_list.append(objects[object]['size'])
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
for folder in files_extracted_from_jar :
    for root, directories, files in os.walk(os.path.join(core_path,folder)) :
        for file in files :
            final_path = os.path.join(root,file)[len(os.path.join(core_path)):].lstrip('\\')
            if final_path not in list and not "\\worldgen\\" in final_path:
                print("File removed:",final_path)
                os.remove(os.path.abspath(os.path.join(core_path,final_path)))

#####################################################################################
# Summary of data
#####################################################################################

with open('file_list.txt','wt') as file_list:
    num = 0
    write_object = "List of all files in the filesystem:\n"
    for item in list :
        write_object = write_object + "\n" + item + ", size: " + str(size_list[num])
        num = num + 1
    file_list.write(write_object)
