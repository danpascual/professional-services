import os
import urllib.request

class MetadataService:
    '''Class to call GCP metadata endpoint to retrieve instance information'''

    @staticmethod
    def get_current_project():
        '''Gets the project id from metadata endpoint or from PROJECT_ID environment variable if set'''
        project_ids = os.environ.get("PROJECT_ID", "")
        if os.environ.get("LOCAL", "") or project_ids:
            return project_ids.split(',')[0]

        url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
        req = urllib.request.Request(url)
        req.add_header("Metadata-Flavor", "Google")
        result = str(urllib.request.urlopen(req).read().decode())
        return result
        