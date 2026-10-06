import textwrap

from PIL import Image, ImageDraw, ImageFont


class MemeGenerator:
    def generate_fresco(self, message: str) -> Image.Image:
        img = Image.open("./assets/images/fresco.jpg")
        font = ImageFont.truetype("./assets/fonts/timesnewromanpsmt.ttf", 20)

        draw = ImageDraw.Draw(img)

        lines = textwrap.wrap(message, width=30)
        text = "\n".join(lines)

        draw.multiline_text(
            (165, 140),
            text,
            fill="black",
            font=font,
            spacing=4,
            anchor="ms",
            align="center",
        )

        return img
