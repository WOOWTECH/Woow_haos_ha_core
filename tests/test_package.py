import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / 'ha_core'

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.config = yaml.safe_load((ADDON / 'config.yaml').read_text())
        self.lock = json.loads((ROOT / 'version-lock.json').read_text())

    def test_repository_identity(self):
        repo = yaml.safe_load((ROOT / 'repository.yaml').read_text())
        self.assertEqual(repo['url'], 'https://github.com/WOOWTECH/Woow_haos_ha_core')
        self.assertEqual(self.config['slug'], 'woow_ha_core')

    def test_versions(self):
        self.assertEqual(self.lock['ha_core_version'], '2026.9.1')
        self.assertEqual(self.config['version'], self.lock['addon_version'])
        self.assertNotEqual(self.config['version'], self.lock['ha_core_version'])

    def test_architecture_pins(self):
        builds = yaml.safe_load((ADDON / 'build.yaml').read_text())
        self.assertEqual(set(self.config['arch']), {'amd64', 'aarch64'})
        self.assertEqual(set(builds['build_from']), set(self.config['arch']))
        for arch, reference in builds['build_from'].items():
            expected = (self.lock['upstream_image'] + ':' + self.lock['ha_core_version']
                        + '@' + self.lock['platforms'][arch]['manifest_digest'])
            self.assertEqual(reference, expected)
        self.assertFalse(builds['squash'])

    def test_restore_friendly_defaults(self):
        self.assertEqual(self.config['boot'], 'manual')
        self.assertEqual(self.config['backup'], 'cold')
        self.assertFalse(self.config['init'])
        self.assertGreaterEqual(self.config['timeout'], 300)
        self.assertIsNone(self.config['ports']['8123/tcp'])

    def test_own_config_only(self):
        self.assertEqual(self.config['map'], ['addon_config:rw'])
        self.assertNotIn('backup_exclude', self.config)
        self.assertEqual(self.config['options'], {})
        self.assertEqual(self.config['schema'], {})

    def test_no_host_access(self):
        for key in ['host_network', 'hassio_api', 'homeassistant_api', 'ingress']:
            self.assertIs(self.config[key], False)
        for key in ['docker_api', 'host_pid', 'host_dbus', 'full_access']:
            self.assertFalse(self.config.get(key, False))
        self.assertFalse(self.config.get('privileged', []))

    def test_no_seed_or_bundled_core(self):
        files = {p.relative_to(ADDON / 'rootfs').as_posix()
                 for p in (ADDON / 'rootfs').rglob('*') if p.is_file()}
        self.assertEqual(files, {'usr/local/bin/ha-core-entrypoint'})
        docker = (ADDON / 'Dockerfile').read_text()
        self.assertFalse(any(line.startswith('RUN ') for line in docker.splitlines()))
        self.assertIn('FROM ${BUILD_FROM}', docker)
        self.assertIn(self.lock['upstream_index_digest'], docker)
        self.assertIn('ENTRYPOINT ["/usr/local/bin/ha-core-entrypoint", "/init"]', docker)
        self.assertEqual(self.lock['verified_upstream_entrypoint'], ['/init'])
        self.assertIsNone(self.lock['verified_upstream_cmd'])

    def test_wrapper_only_filters_supervisor_environment(self):
        with tempfile.TemporaryDirectory() as d:
            sentinel = Path(d) / 'restored-config'
            sentinel.write_bytes(b'unchanged restored data')
            before = hashlib.sha256(sentinel.read_bytes()).hexdigest()
            env = dict(os.environ)
            for key in ['SUPERVISOR_TOKEN', 'HASSIO_TOKEN', 'HASSIO', 'SUPERVISOR']:
                env[key] = 'synthetic-test-only'
            env['KEEP_ME'] = 'unchanged'
            code = ('import json,os,sys;print(json.dumps({"keep":os.getenv("KEEP_ME"),'
                    '"tokens":[k for k in ["SUPERVISOR_TOKEN","HASSIO_TOKEN","HASSIO","SUPERVISOR"]'
                    ' if k in os.environ],"args":sys.argv[1:]}))')
            p = subprocess.run(['sh', str(ADDON / 'rootfs/usr/local/bin/ha-core-entrypoint'),
                                sys.executable, '-c', code, 'with spaces', ';literal'],
                               env=env, cwd=d, capture_output=True, text=True, timeout=10)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout), {'keep': 'unchanged', 'tokens': [],
                                                   'args': ['with spaces', ';literal']})
            self.assertEqual(hashlib.sha256(sentinel.read_bytes()).hexdigest(), before)

    def test_k3s_version_overlay(self):
        values = yaml.safe_load((ROOT / 'examples/k3s-values.2026.9.1.yaml').read_text())
        self.assertEqual(values['homeassistant']['image']['tag'], self.lock['ha_core_version'])
        self.assertEqual(values['homeassistant']['image']['repository'], self.lock['upstream_image'])
        self.assertFalse(values['postgres']['enabled'])
        secret = yaml.safe_load((ROOT / 'examples/k3s-empty-secret.yaml').read_text())
        self.assertEqual(secret['metadata']['name'], values['secrets']['existingSecretName'])
        self.assertEqual(secret['data'], {})

if __name__ == '__main__':
    unittest.main()
