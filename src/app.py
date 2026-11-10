import gradio as gr

from recognizer import recognize

TITLE = "# GraphoMindAI"
DESCRIPTION = (
    "Распознавание рукописного текста по фотографии. "
    "Загрузите фото или сделайте снимок и нажмите «Распознать»."
)
HINT = (
    "**Подсказки:** лучше всего распознаётся одно слово или короткая строка. "
    "Фото должно быть чётким, без бликов и теней."
)


def predict(image):
    if image is None:
        return "Сначала загрузите фото."
    return recognize(image)


def clear():
    return None, ""


with gr.Blocks() as demo:
    gr.Markdown(TITLE)
    gr.Markdown(DESCRIPTION)

    with gr.Row():
        image_in = gr.Image(
            type="pil",
            label="Фото рукописного текста",
            sources=["upload", "webcam"],
        )
        text_out = gr.Textbox(label="Распознанный текст", lines=8, interactive=False)

    with gr.Row():
        run_btn = gr.Button("Распознать", variant="primary")
        clear_btn = gr.Button("Очистить")

    gr.Markdown(HINT)

    run_btn.click(predict, inputs=image_in, outputs=text_out)
    clear_btn.click(clear, outputs=[image_in, text_out])


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())