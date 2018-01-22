from dropbox import Dropbox
from dropbox.files import FileMetadata, FolderMetadata
from rq import get_current_job
from rq.job import Job, NoSuchJobError

def human_readable(bytes):
    if bytes < 1024:
        return "%.0f Bytes" % bytes
    elif bytes < 1048576:
        return "%.2f KB" % (bytes / 1024)
    elif bytes < 1073741824:
        return "%.2f MB" % (bytes / 1048576)
    else:
        return "%.2f GB" % (bytes / 1073741824)

def get_entries_of_folder(client, folder_path):
    list_folder_result = client.files_list_folder(folder_path)
    all_entries = list_folder_result.entries
    while list_folder_result.has_more:
        list_folder_result = client.files_list_folder_continue(list_folder_result.cursor)
        all_entries += list_folder_result.entries
    return all_entries

def walk(client, metadata, bytes_read, total_bytes):
    job = get_current_job()
    if isinstance(metadata, FileMetadata):
        size_bytes = metadata.size
        bytes_read += int(size_bytes)
        update_progress(job, float(bytes_read) / total_bytes, metadata.name)
        return {'name': metadata.name, 'value': size_bytes}, bytes_read
    elif isinstance(metadata, FolderMetadata):
        result, bytes_read = walk_folder(client, metadata.path_lower, metadata.name, bytes_read, total_bytes)
        # empty directories? do we care?
        if len(result['children']) is 0:
            result.pop('children', None)
        return result, bytes_read
    else:
        raise Exception('Unknown metadata type: %s' % str(metadata))

def walk_folder(client, full_path, path_basename, bytes_read, total_bytes):
    result = {'name': path_basename, 'children': [], 'value': 0}
    all_entries = get_entries_of_folder(client, full_path)
    for entry in all_entries:
        # Skip hidden files, shit gets too rowdy
        if entry.name.startswith('.'):
            continue
        child, bytes_read = walk(client, entry, bytes_read, total_bytes)
        result['children'].append(child)
    return result, bytes_read

def walk_entire_dropbox(access_token, total_bytes):
    client = Dropbox(access_token)
    return walk_folder(client, '', '/', 0, total_bytes)

def update_progress(job, progress, current_path):
    progress_int = int(progress * 100)
    job.meta['progress'] = progress_int
    job.meta['current'] = current_path
    job.save()

def get_job_from_key(key, conn):
    job_key = key.replace("rq:job:", "")
    try:
        job = Job.fetch(job_key, connection=conn)
    except NoSuchJobError, e:
        return None
    return job
