#
# ========================================================
# Copyright (c) 2012 Whamcloud, Inc.  All rights reserved.
# ========================================================


import threading
from cluster_sim.log import log
from cluster_sim.utils import Persisted


class FakeCluster(Persisted):
    filename = 'cluster.json'
    default_state = {
        'nodes': {},
        'resources': {}
    }

    def __init__(self, path):
        super(FakeCluster, self).__init__(path)
        self._lock = threading.Lock()

    def get_by_uuid(self, uuid):
        with self._lock:
            for ha_label, resource in self.state['resources'].items():
                if resource['uuid'] == uuid:
                    return resource

            raise KeyError(uuid)

    def clear_resources(self):
        with self._lock:
            self.state['resources'] = {}
            self.save()

    def resource_locations(self):
        with self._lock:
            locations = {}
            for ha_label, resource in self.state['resources'].items():
                locations[ha_label] = resource['started_on']

            return locations

    def get_running_resources(self, nodename):
        with self._lock:
            return [resource for resource in self.state['resources'].values() if resource['started_on'] == nodename]

    def start(self, ha_label):
        with self._lock:
            resource = self.state['resources'][ha_label]
            resource['started_on'] = resource['primary_node']
            log.debug("Starting resource %s on %s" % (ha_label, resource['primary_node']))
            self.save()
            return resource

    def stop(self, ha_label):
        with self._lock:
            resource = self.state['resources'][ha_label]
            resource['started_on'] = None
            self.save()
            return resource

    def failover(self, ha_label):
        with self._lock:
            resource = self.state['resources'][ha_label]
            resource['started_on'] = resource['secondary_node']
            self.save()
            return resource

    def failback(self, ha_label):
        with self._lock:
            resource = self.state['resources'][ha_label]
            resource['started_on'] = resource['primary_node']
            self.save()
            return resource

    def leave(self, nodename):
        with self._lock:
            log.debug("leave: %s" % nodename)
            for ha_label, resource in self.state['resources'].items():
                if resource['started_on'] == nodename:
                    options = set([resource['primary_node'], resource['secondary_node']]) - set([nodename])
                    if options:
                        destination = options.pop()
                        log.debug("migrating %s to %s" % (ha_label, destination))
                        resource['started_on'] = destination
                    else:
                        log.debug("stopping %s" % (ha_label))
                        resource['started_on'] = None

            self.save()

    def join(self, nodename):
        with self._lock:
            if not nodename in self.state['nodes']:
                self.state['nodes'][nodename] = {}

            for ha_label, resource in self.state['resources'].items():
                if resource['started_on'] is None:
                    if resource['primary_node'] == nodename:
                        log.debug("Starting %s on primary %s" % (ha_label, nodename))
                        resource['started_on'] = nodename
                    elif resource['secondary_node'] == nodename:
                        log.debug("Starting %s on secondary %s" % (ha_label, nodename))
                        resource['started_on'] = nodename
            self.save()

    def configure(self, nodename, device_path, ha_label, uuid, primary, mount_point):
        with self._lock:
            try:
                resource = self.state['resources'][ha_label]
            except KeyError:
                resource = {
                    'ha_label': ha_label,
                    'device_path': device_path,
                    'uuid': uuid,
                    'primary_node': None,
                    'secondary_node': None,
                    'mount_point': mount_point,
                    'started_on': None
                }

            if primary:
                resource['primary_node'] = nodename
            else:
                resource['secondary_node'] = nodename
            self.state['resources'][ha_label] = resource
            self.save()

    def unconfigure(self, nodename, ha_label, primary):
        with self._lock:
            try:
                resource = self.state['resource'][ha_label]
            except KeyError:
                return
            else:
                if primary:
                    del self.state['resource'][ha_label]
                else:
                    resource['secondary_node'] = None

                self.save()
