from flask import Blueprint
from flask import current_app, request
from flask import render_template, jsonify
from functools import wraps
import docker
from cluster import Cluster

dashboard_app = Blueprint('dashboard_app', __name__,
        template_folder='templates',
        static_folder='static',
        )


@dashboard_app.before_app_first_request
def setup_cluster():
    docker_url = 'unix://var/run/docker.sock'
    docker_version = '0.6.5'
    db_name = 'cluster.db'
    if current_app.config.get('DOCKER_URL'):
        docker_url = current_app.config.get('DOCKER_URL')
    if current_app.config.get('DOCKER_VERSION'):
        docker_version = current_app.config.get('DOCKER_VERSION')
    if current_app.config.get('DB_NAME'):
        db_name = current_app.config.get('DB_NAME')
    try:
        #current_app.docker_conn = docker.Client(base_url=docker_url, version=docker_version)
        current_app.cluster = Cluster(docker_url, docker_version, db_name)
    except Exception as e:
        print e

@dashboard_app.route('/', methods=['GET', 'POST'])
def overview():
    if request.method == 'POST':
        cluster = []
        hosts = request.form.getlist('host[]')
        ips = request.form.getlist('ip[]')
        services = request.form.getlist('services[]')

        for pos, image in enumerate(request.form.getlist('image[]')):
            node = {
                'image': image,
                'hostname': hosts[pos],
                'ip': ips[pos],
                'services': [service[service.find('-') + 1:] for service in services if service[0:service.find('-')] == str(pos + 1)]
            }
            cluster.append(node)

        for node_started in current_app.cluster.start_cluster(cluster):
            print 'NODE STARTED: ', node_started

    running = current_app.cluster.list_cluster()
    return render_template('main.html', running=running)

@dashboard_app.route('/container/<container_id>')
def inspect(container_id):
    container = current_app.cluster.container_detail(container_id)
    return render_template('detail.html', container=container)

@dashboard_app.route('/container/<container_id>/stop', methods=['POST'])
def stop(container_id):
    try:
        resp = current_app.cluster.stop_container(container_id)
        return jsonify(dict(response='Container %s stopped' % container_id, status=200))
    except docker.APIError as e:
        print("Docker APIError: %s" % e)
        return jsonify(dict(response='Container %s not found' % container_id, status=404)), 404

@dashboard_app.route('/container/<container_id>/kill', methods=['POST'])
def kill(container_id):
    try:
        resp = current_app.cluster.kill_container(container_id)
        return jsonify(dict(response='Container %s killed' % container_id, status=200))
    except docker.APIError as e:
        print("Docker APIError: %s" % e)
        return jsonify(dict(response='Container %s not found' % container_id, status=404)), 404

