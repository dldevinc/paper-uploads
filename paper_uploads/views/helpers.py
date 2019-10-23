import os
import uuid
import shutil
import tempfile
from typing import Optional, Dict, Any, Iterable, Union, List, IO, Type, TypeVar
from django.http import JsonResponse
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.contrib.contenttypes.models import ContentType
from .. import exceptions

T = TypeVar('T')


def success_response(data: Optional[Dict[str, Any]] = None) -> JsonResponse:
    data = data or {}
    data['success'] = True
    return JsonResponse(data)


def error_response(errors: Union[str, Iterable[str]] = '', prevent_retry: bool = True) -> JsonResponse:
    if not errors:
        errors = []
    elif not isinstance(errors, (list, tuple)):
        errors = [errors]

    data = {
        'success': False,
        'errors': errors,
        'preventRetry': prevent_retry
    }
    return JsonResponse(data)


def get_exception_messages(exception: ValidationError) -> List[str]:
    messages = []
    for msg in exception:
        if isinstance(msg, tuple):
            field, errors = msg
            if field == NON_FIELD_ERRORS:
                for error in reversed(errors):
                    messages.insert(0, error)
            else:
                messages.extend(
                    "'{}': {}".format(field, error) for error in errors
                )
        else:
            messages.append(msg)
    return messages


def read_file(request) -> IO:
    """
    Загрузка файла с поддержкой chunks.
    """
    try:
        chunk_index = int(request.POST['qqpartindex'])
        total_chunks = int(request.POST['qqtotalparts'])
    except KeyError:
        chunk_index = 0
        total_chunks = 1
    except (ValueError, TypeError):
        raise exceptions.InvalidChunking

    try:
        uid = uuid.UUID(request.POST.get('qquuid'))
    except (AttributeError, ValueError):
        raise exceptions.InvalidUUID

    tempfilepath = os.path.join(tempfile.gettempdir(), 'upload_{}'.format(uid))
    file = request.FILES.get('qqfile')
    if file is None:    # бывает при отмене загрузки на медленном интернете
        if os.path.isfile(tempfilepath):
            os.unlink(tempfilepath)
        raise exceptions.UncompleteUpload

    if total_chunks > 1:
        with open(tempfilepath, 'a+b') as fp:
            shutil.copyfileobj(file, fp, 1024 * 1024)

        if chunk_index < total_chunks - 1:
            raise exceptions.ContinueUpload

        file = open(tempfilepath, 'rb')

    return file


def get_model_class(content_type_id: int, base_class: Type[T]) -> Type[T]:
    """
    Получение класса модели загружаемого файла по ContentType ID.
    """
    try:
        content_type = ContentType.objects.get(pk=content_type_id)
    except ContentType.DoesNotExist:
        raise exceptions.InvalidContentType(content_type_id)

    model_class = content_type.model_class()
    if issubclass(model_class, base_class):
        return model_class

    raise exceptions.InvalidContentType(content_type_id)


def get_instance(model_class: Type[T], instance_id: int) -> T:
    """
    Получение экземпляра модели загружаемого файла.
    """
    try:
        instance_id = int(instance_id)
    except (ValueError, TypeError):
        raise exceptions.InvalidObjectId(instance_id)
    else:
        return model_class._default_manager.get(pk=instance_id)
