import litellm
import gradio as gr
import requests
import os
from PIL import Image
from io import BytesIO

# 设置 API 密钥
os.environ["OPENAI_API_KEY"] = "sk-8QabjM9ZrgvuMHyqF62427D9EbA84a14986d537f16B0Ff73"  # 替换为您的实际 API 密钥

# 获取聊天机器人响应
def get_response(message):
    try:
        response = litellm.completion(
            model="openai/gpt-3.5-turbo",
            api_key=os.environ["OPENAI_API_KEY"],
            api_base="https://burn.hair/v1",
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# 生成语音文件
def generate_speech(text, speech_file_path="speech.mp3"):
    try:
        response = litellm.speech(
            model="openai/tts-1",
            voice="alloy",
            input=text,
            api_key=os.environ["OPENAI_API_KEY"],
            api_base="https://burn.hair/v1",
            organization=None,
            project=None,
            max_retries=1,
            timeout=600,
            client=None,
            optional_params={},
        )
        response.stream_to_file(speech_file_path)
        return speech_file_path
    except Exception as e:
        return f"Error: {str(e)}"

# 获取实时天气信息
def get_weather():	
    url = "https://api.caiyunapp.com/v2.6/91EGzpV4OgclrP3T/113.3954,23.0394/weather?dailysteps=3&hourlysteps=48"#需要自己找到经纬度，替换掉url里面的经纬度
    response = requests.get(url)
    weather_data = response.json()
    if weather_data["status"] == "ok":
        timezone = weather_data['timezone'],
        realtime = weather_data["result"]["realtime"]
        temperature = realtime["temperature"]
        humidity = realtime["humidity"]
        skycon = realtime["skycon"]
        aqi = realtime["air_quality"]["aqi"]["chn"]
        weather_info = "广东工业大学大学城校区天气\n"+f"温度: {temperature}°C\n湿度: {humidity*100}%\n天气: {skycon}\n空气质量指数 (AQI): {aqi}"
        return weather_info
    else:
        return "无法获取天气信息"

# 生成相关图片（文生图）
def generate_image(message):
    try:
        response = litellm.image_generation(
            model='openai/dall-e-3', 
            prompt=message,
            api_key=os.environ["OPENAI_API_KEY"],
            api_base="https://burn.hair/v1",
            organization=None,
            max_retries=1,
            timeout=600,
        )
        return response['data'][0]['url']  # 返回图片URL
    except Exception as e:
        return f"Error: {str(e)}"

# Gradio处理函数 - 聊天机器人
def chat_with_bot(message, play_audio):
    text_response = get_response(message)
    if play_audio:
        audio_file_path = generate_speech(text_response)
        return text_response, audio_file_path
    else:
        return text_response, None

# Gradio处理函数 - 文本转语音
def text_to_speech(text):
    audio_file_path = generate_speech(text)
    return audio_file_path

# Gradio处理函数 - 天气查询
def weather_query(play_audio):
    weather_info = get_weather()
    if play_audio:
        audio_file_path = generate_speech(weather_info)
        return weather_info, audio_file_path
    else:
        return weather_info, None

# 点击计数
counter = 0
# 点击计数处理函数
def increment_counter():
    global counter
    counter += 1
    return counter

# Gradio处理函数 - 文生图
def text_to_image(prompt):
    image_url = generate_image(prompt)
    if "Error:" in image_url:
        return image_url  # 返回错误信息
    try:
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))
        return image
    except Exception as e:
        return f"Error: {str(e)}"

# 定义Gradio界面
chatbot_interface = gr.Interface(
    fn=chat_with_bot,
    inputs=[
        gr.Textbox(label="Message"),
        gr.Checkbox(label="Play Audio")
    ],
    outputs=[
        gr.Textbox(label="Response"),
        gr.Audio(label="Audio Response", type="filepath")
    ],
    title="Chat with Bot",
    description="Enter a message to chat with the bot and get a response. Check the box to get an audio response."
)

text_to_speech_interface = gr.Interface(
    fn=text_to_speech,
    inputs=gr.Textbox(label="Text to Convert to Speech"),
    outputs=gr.Audio(label="Audio Response", type="filepath"),
    title="Text to Speech",
    description="Enter text to convert it to speech."
)

def weather_and_counter_query(play_audio):
    weather_info, audio_path = weather_query(play_audio)
    new_count = increment_counter()
    return weather_info, audio_path, new_count

weather_interface = gr.Interface(
    fn=weather_and_counter_query,
    inputs=gr.Checkbox(label="Play Audio"),
    outputs=[
        gr.Textbox(label="Weather Information"),
        gr.Audio(label="Audio Response", type="filepath"),
        gr.Textbox(label="Click Count", interactive=False)
    ],
    title="Weather Query",
    description="Get the current weather information and track clicks. Check the box to get an audio response."
)

image_generation_interface = gr.Interface(
    fn=text_to_image,
    inputs=gr.Textbox(label="Image Prompt"),
    outputs=gr.Image(label="Generated Image"),
    title="Text to Image",
    description="Enter a prompt to generate an image."
)

# 创建Tab布局
demo = gr.TabbedInterface(
    interface_list=[chatbot_interface, text_to_speech_interface, weather_interface, image_generation_interface],
    tab_names=["Chat with Bot", "Text to Speech", "Weather Query", "Text to Image"]
)

if __name__ == "__main__":
    demo.launch(share=True)