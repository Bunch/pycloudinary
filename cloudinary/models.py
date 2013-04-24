from cloudinary import forms, utils
from cloudinary.storage import CloudinaryStorage
from django.db import models
from django.db.models.fields.files import ImageFieldFile

# Ensure South doesn't explode on this field
try:
    import south.modelsinspector
except ImportError:
    pass
else:
    south.modelsinspector.add_introspection_rules(
        [],
        ["^cloudinary\.models\.CloudinaryField"]
    )


class CloudinaryFieldFile(ImageFieldFile):
    
  closed = True

  def save(self, name, content, save=True):
    # Allow strings (URLs) to be saved as files
    if isinstance(content, str):
        content = StringWithSize(content)

    super(CloudinaryFieldFile, self).save(name, content, save)

  def url_with_options(self, **options):
    return utils.cloudinary_url(self.name, **options)[0]
    
  def _get_image_dimensions(self):
      if not hasattr(self, '_dimensions_cache'):
          self._dimensions_cache = get_image_dimensions(self)
      return self._dimensions_cache
      
      
def get_image_dimensions(file_or_path):
    """
    Returns the (width, height) of an image, given an open file or a path.  Set
    'close' to True to close the file at the end if it is initially in an open
    state.
    """
    # Try to import PIL in either of the two ways it can end up installed.
    import ImageFile as PILImageFile

    p = PILImageFile.Parser()
    file = file_or_path
    try:
        # Most of the time PIL only needs a small chunk to parse the image and
        # get the dimensions, but with some TIFF files PIL needs to parse the
        # whole file.
        chunk_size = 1024
        while 1:
            data = file.read(chunk_size)
            if not data:
                break
            p.feed(data)
            if p.image:
                return p.image.size
            chunk_size = chunk_size*2
        return None
    except:
        return [0, 0]
    finally:
        file.close()


# This is necessary so we can easily save URLs in the DB
class StringWithSize(str):
  size = 0


class CloudinaryField(models.ImageField):

  attr_class = CloudinaryFieldFile
  description = "An image stored in Cloudinary"

  def __init__(self, *args, **kwargs):
    for arg in ('storage', 'upload_to'):
        if arg in kwargs:
            raise TypeError("'%s' cannot be modified for %s." % (arg, self.__class__))

    options = {
      'storage': CloudinaryStorage(kwargs.pop('upload_options', {})),
      'upload_to': '/',
    }
    options.update(kwargs)
    super(CloudinaryField, self).__init__(*args, **options)
