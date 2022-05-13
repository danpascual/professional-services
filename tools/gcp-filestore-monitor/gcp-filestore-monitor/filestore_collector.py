from prometheus_client.core import GaugeMetricFamily

class FilestoreCollector(object):
    
    def __init__(self, metrics):
        self.metrics = metrics

    def describe(self):
        return []
    
    def collect(self):
        """Collect prometheus metrics"""
        usage_gauge = GaugeMetricFamily('gcp_filestore_usage_percentage', 'Usage percentage of GCP Filestore volumes', labels=['project', 'name', 'location', 'volume'])

        for current in self.metrics:
            usage_gauge.add_metric([current['project'], current['instance_sname'], current['location'], current['vol_name']], current['USED_PERCENTAGE'])
        
        yield usage_gauge
