import zipfile
import tempfile

from cowidev.utils.web.download import download_file_from_url


def extract_zip(input_path, output_folder, **kwargs):
    if input_path.startswith("http"):
        with tempfile.NamedTemporaryFile() as tf:
            download_file_from_url(input_path, tf.name, **kwargs)
            z = zipfile.ZipFile(tf.name)
    else:
        z = zipfile.ZipFile(input_path)
    z.extractall(output_folder)
