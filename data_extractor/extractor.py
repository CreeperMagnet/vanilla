# Import proper libraries
import urllib.request, json, math, re, os, shutil

#####################################################################################
# User-defined variables
#####################################################################################

# The link to Mojang's version manifest. This probably shouldn't change.
manifest_url = 'http://launchermeta.mojang.com/mc/game/version_manifest.json'

#####################################################################################
# Extracting cached data from resource links using index off the internet
#####################################################################################

def json_from_url(url) :
    return json.loads(urllib.request.urlopen(url).read())

version_manifest = json_from_url(manifest_url)
latest_version_data = json_from_url(version_manifest['versions'][0]['url'])
index = json_from_url(latest_version_data['assetIndex']['url'])
number = 0
for object in index['objects'] :
    if not object.startswith('icons/') :
        hash = index['objects'][object]['hash']
        destination_path = os.path.abspath(os.path.join("..","assets",object))
        os.makedirs(os.path.dirname(destination_path), exist_ok = True)
        try :
            size = os.path.getsize(destination_path)
            if size == index['objects'][object]['size'] :
                continue
        except :
            pass
        object_url = "https://resources.download.minecraft.net/"+hash[:2]+"/"+hash
        print("Downloading:",object_url)
        urllib.request.urlretrieve(object_url, destination_path)
        number = number + 1
print(number,"new files downloaded")


#
##wait = input("Press enter when you have updated the jar files located in this directory.")
#
##os.system("java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --server --reports --output data")
#
#print("Operations completed")
