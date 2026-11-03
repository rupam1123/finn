"""Private single-document subprocess entrypoint; no network or database writes."""
import json
import sys

from .documents import _extract_document_worker


def main():
    limit=80_000_000 if len(sys.argv)>3 and sys.argv[3] in {'sections','image'} else 30_000_000
    body = sys.stdin.buffer.read(limit+1)
    if len(body) > limit:
        raise ValueError('PDF size limit exceeded')
    if len(sys.argv)>3 and sys.argv[3]=='image':
        import base64,hashlib
        from .pdf_runtime import pymupdf
        with pymupdf.open(stream=body,filetype='pdf') as doc:
            index=int(sys.argv[2])-1
            if index<0 or index>=len(doc):raise ValueError('Unknown primary page')
            pix=doc[index].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False)
            png=pix.tobytes('png')
            if len(png)>8_000_000:raise ValueError('Page image exceeds input budget')
        result={'page':index+1,'mime_type':'image/png','data':base64.b64encode(png).decode(),
                'image_sha256':hashlib.sha256(png).hexdigest()}
    else:
        result = _extract_document_worker(body, sys.argv[1], int(sys.argv[2]),len(sys.argv)>3 and sys.argv[3]=='sections')
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8'))


if __name__ == '__main__':
    main()
