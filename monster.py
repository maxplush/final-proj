import os
import requests
from monsterapi import client

# Initialize the client with the API key from environment variables
api_key = os.environ.get("MONSTER_API_KEY")
monster_client = client(api_key)

# Define the model and input data
model = 'txt2img'
input_data = {
    'prompt': "Illustrate a dramatic scene of a motorcyclist on a Yamaha 550 Enduro, speeding along a dimly lit, rain-slicked road in Colorado. The setting is a warm summer night with light rain, glistening off the pavement and creating a moody atmosphere. The motorcyclist, wearing an unfastened helmet, is caught in a tense moment as he makes the decision to lay the bike down, avoiding an oncoming solid wood fence. Show the bike skidding on its side, the rider's limbs extended to brace the impact, and a look of intense focus and fear on his face. Capture the moment just before he tumbles, highlighting the danger and near-tragic intensity. In the background, suggest the peaceful Colorado neighborhood with a soft glow from porch lights, emphasizing the contrast between the quiet environment and the fast-paced, life-altering moment.",
    'negprompt': 'deformed, bad anatomy, disfigured, poorly drawn face',
    'samples': 1,
    'steps': 50,
    'aspect_ratio': 'square',
    'guidance_scale': 7.5,
    'seed': 2414,
}

# Generate content
result = monster_client.generate(model, input_data)
image_urls = result['output']

# Folder to save the images
output_folder = '/Users/maxplush/Documents/ragnews-new/gen_image'
os.makedirs(output_folder, exist_ok=True)

# Download and save each image
for idx, url in enumerate(image_urls):
    image_data = requests.get(url).content
    image_path = os.path.join(output_folder, f'image_{idx}.png')
    with open(image_path, 'wb') as image_file:
        image_file.write(image_data)
    print(f"Image saved at {image_path}")
