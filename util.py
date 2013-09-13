import os, time
from rq import get_current_job
from rq.job import Job, NoSuchJobError
from flask import session

def human_readable(bytes):
    if bytes < 1024:
        return "%.0f Bytes" % bytes;
    elif bytes < 1048576:
        return "%.2f KB" % (bytes / 1024)
    elif bytes < 1073741824:
        return "%.2f MB" % (bytes / 1048576)
    else:
        return "%.2f GB" % (bytes / 1073741824)

def walk(client, metadata, bytes_read, total_bytes):
    job = get_current_job()
    dir_path = os.path.basename(metadata['path'])
    bytes = metadata['bytes']
    bytes_read += int(bytes)
    update_progress(job, float(bytes_read) / total_bytes, dir_path)

    result = {'name':os.path.basename(dir_path), 'children':[], 'value':bytes}

    if 'contents' in metadata:
        for dir_entry in metadata['contents']:
            path = dir_entry['path']
            # Skip hidden files, shit gets too rowdy
            if os.path.basename(path)[0] == '.':
                continue
            dir_entry_bytes = dir_entry['bytes']
            bytes_read += int(dir_entry_bytes)
            update_progress(job, float(bytes_read) / total_bytes, path)
            if dir_entry_bytes is 0:
                child, bytes_read = walk(client, get_metadata(client, path), bytes_read, total_bytes)
            else:
                child = {'name':os.path.basename(path), 'value':dir_entry_bytes}
            result['children'].append(child)
    #empty directories? do we care?
    if len(result['children']) is 0:
        _ = result.pop('children', None)
    return result, bytes_read

def get_metadata(client, path):
    backoff = 0.5
    while True:
        try:
            metadata = client.metadata(path)
            return metadata
        except ErrorResponse, e:
            #exponential back off to appease api limits
            time.sleep(backoff)
            backoff *= 2
            continue

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
