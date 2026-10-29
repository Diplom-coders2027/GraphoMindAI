import gradio as gr
from recognizer import recognize

demo = gr.Interface(
    fn=recognize,
    inputs=gr.Image(type="pil", label="Фото рукописного текста"),
    outputs=gr.Textbox(label="Распознанный текст"),
    title="GraphoMindAI",
)
demo.launch()