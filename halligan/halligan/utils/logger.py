import io
import os
import sys
import base64
import hashlib
import platform
from pathlib import Path
from timeit import default_timer as timer
from datetime import datetime, timezone

from importlib.metadata import distributions
import nbformat as nbf
import PIL.Image


def get_python_version() -> str:
    version_info = sys.version_info
    major, minor, micro, releaselevel, serial = version_info
    return f"{major}.{minor}.{micro}-{releaselevel}{serial}"


def get_python_env_hash() -> str:
    installed_packages = {dist.metadata['Name'].lower(): dist.version for dist in distributions()}
    package_list = sorted(f"{pkg}=={version}" for pkg, version in installed_packages.items())
    packages_str = "\n".join(package_list)
    hash_object = hashlib.sha256(packages_str.encode('utf-8'))
    return hash_object.hexdigest()


def get_image_tag(image: PIL.Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode()
    return f'<img src="data:image/png;base64,{image_b64}"/>'


def get_image_grid(images: list[PIL.Image.Image], image_captions: list[str], columns = 5) -> str:
    image_htmls = []
    for image, caption in zip(images, image_captions):
        image_html = f'<div>{get_image_tag(image)}<p>{caption}</p></div>'
        image_htmls.append(image_html)

    return f'''
    <div style="
        display: grid; 
        grid-template-columns: repeat({columns}, auto);
        column-gap: 10px;
        row-gap: 10px;">
        {"".join(image_htmls)}
    </div>
    '''


PYTHON_VERSION = get_python_version()
PYTHON_ENV_HASH = get_python_env_hash()


class Trace:
    tracing = False

    @classmethod
    def start(cls, captcha: PIL.Image.Image, path: str = None) -> None:
        cls.notebook = nbf.v4.new_notebook()
        cls.timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        header = (
            "# Execution Trace\n"
            f"- **Start Timestamp (UTC)**: {datetime.now(timezone.utc).isoformat()}\n"
            f"- **OS**: {platform.system()} {platform.release()} {platform.version()}\n"
            f"- **Machine**: {platform.machine()}\n"
            f"- **Python Info**: {PYTHON_VERSION}\n"
            f"- **Python Environment Hash**: {PYTHON_ENV_HASH}\n"
            f"- **CAPTCHA**:\n\n"
            f"{get_image_tag(captcha)}"
        )
        cls.cells: list = cls.notebook.get("cells", [])
        cls.cells.append(
            nbf.v4.new_markdown_cell(header)
        )
        cls.tracing = True
        cls.path = path

    @classmethod
    def agent(cls):
        def decorator(func):
            def wrapper(self, prompt: str, images: list[PIL.Image.Image] = [], image_captions: list[str] = []):
                if not cls.tracing:
                    return func(self, prompt, images, image_captions)

                start_time = timer()
                response, metadata = func(self, prompt, images, image_captions)
                end_time = timer()
                execution_time = end_time - start_time

                prompt_cell = nbf.v4.new_code_cell(source=f"PROMPT = '''\n{prompt}\n'''")
                images_cell = nbf.v4.new_code_cell(source=f"IMAGES = {len(images)}", outputs=[
                    nbf.v4.new_output(
                        output_type="display_data", 
                        data={"text/html": get_image_grid(images, image_captions)}, 
                        metadata={}
                    )
                ])

                metadata = "\n".join(f"{key.upper()} = {value}" for key, value in metadata.items())
                response = f"RESPONSE = '''\n{response}\n'''\nTIME = {execution_time}\n" + metadata
                response_cell = nbf.v4.new_code_cell(source=response)
                divider_cell = nbf.v4.new_markdown_cell(f"---")
                cls.cells.extend([prompt_cell, images_cell, response_cell, divider_cell])

                return response, metadata
            return wrapper
        return decorator   

    @classmethod
    def section(cls, title: str):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not cls.tracing:
                    return func(*args, **kwargs)

                cell = nbf.v4.new_markdown_cell(f"## {title}")
                cls.cells.append(cell)

                start_time = timer()
                result = func(*args, **kwargs)
                end_time = timer()
                execution_time = end_time - start_time

                cell = nbf.v4.new_markdown_cell(f"**Section Time:** {execution_time:.3f} seconds")
                cls.cells.append(cell)

                return result
            return wrapper
        return decorator
    
    @classmethod
    def comment(cls, markdown: str):
        cell = nbf.v4.new_markdown_cell(markdown)
        cls.cells.append(cell)

    @classmethod
    def stop(cls):
        if cls.path:
            directory = os.path.dirname(cls.path)
            os.makedirs(directory, exist_ok=True)
            nbf.write(cls.notebook, cls.path)
        else:
            name = f"trace-{cls.timestamp}.ipynb"
            nbf.write(cls.notebook, name)

        cls.notebook = None
        cls.cells = None
        cls.timestamp = None
        cls.tracing = False