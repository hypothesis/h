#!groovy

node {
    // -------------------------------------------------------------------------
    stage 'Build'

    checkout scm

    buildVersion = sh(
        script: 'python -c "import h; print(h.__version__)"',
        returnStdout: true
    ).trim()

    // Docker tags may not contain '+'
    dockerTag = buildVersion.replace('+', '-')

    // Set build metadata
    currentBuild.displayName = buildVersion
    currentBuild.description = "Docker: ${dockerTag}"

    // Build docker image
    sh "make docker DOCKER_TAG=${dockerTag}"
    img = docker.image "hypothesis/hypothesis:${dockerTag}"

    // -------------------------------------------------------------------------
    stage 'Test'

    hostIp = sh(script: 'facter ipaddress_eth0', returnStdout: true).trim()

    postgres = docker.image('postgres:9.4').run('-P -e POSTGRES_DB=htest')
    databaseUrl = "postgresql://postgres@${hostIp}:${containerPort(postgres, 5432)}/htest"

    elasticsearch = docker.image('nickstenning/elasticsearch-icu').run('-P')
    elasticsearchHost = "http://${hostIp}:${containerPort(elasticsearch, 9200)}"

    rabbit = docker.image('rabbitmq').run('-P')
    brokerUrl = "amqp://guest:guest@${hostIp}:${containerPort(rabbit, 5672)}//"

    try {
        // Run our Python tests inside the built container
        img.inside("-u root " +
                   "-e BROKER_URL=${brokerUrl} " +
                   "-e ELASTICSEARCH_HOST=${elasticsearchHost} " +
                   "-e TEST_DATABASE_URL=${databaseUrl}") {
            // Test dependencies
            sh 'apk-install build-base libffi-dev postgresql-dev python-dev'
            sh 'pip install -q tox'

            // Unit tests
            sh 'cd /var/lib/hypothesis && tox'
            // Functional tests
            sh 'cd /var/lib/hypothesis && tox -e functional'
        }
    } finally {
        rabbit.stop()
        elasticsearch.stop()
        postgres.stop()
    }

    // We only push the image to the Docker Hub if we're on master
    if (env.BRANCH_NAME != 'master') {
        return
    }

    // -------------------------------------------------------------------------
    stage 'Push'

    docker.withRegistry('', 'docker-hub-build') {
        img.push()
        img.push('latest')
    }
}

def containerPort(container, port) {
    return sh(
        script: "docker port ${container.id} ${port} | cut -d: -f2",
        returnStdout: true
    ).trim()
}
