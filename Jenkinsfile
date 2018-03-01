#!groovy

@Library('pipeline-library') _

def img

node {
    stage('build') {
        checkout(scm)
        img = buildApp(name: 'hypothesis/hypothesis')
    }

    stage('test') {
        hostIp = sh(script: 'facter ipaddress_eth0', returnStdout: true).trim()

        postgres = docker.image('postgres:9.4').run('-P -e POSTGRES_DB=htest')
        databaseUrl = "postgresql://postgres@${hostIp}:${containerPort(postgres, 5432)}/htest"

        elasticsearch_old = docker.image('nickstenning/elasticsearch-icu').run('-P', "-Des.cluster.name=${currentBuild.displayName}")
        elasticsearchHost_old = "http://${hostIp}:${containerPort(elasticsearch_old, 9200)}"

        elasticsearch = docker.image('hypothesis/elasticsearch').run('-P -e "discovery.type=single-node"')
        elasticsearchHost = "http://${hostIp}:${containerPort(elasticsearch, 9200)}"

        rabbit = docker.image('rabbitmq').run('-P')
        brokerUrl = "amqp://guest:guest@${hostIp}:${containerPort(rabbit, 5672)}//"

        try {
            testApp(image: img, runArgs: "-u root " +
                                         "-e BROKER_URL=${brokerUrl} " +
                                         "-e ELASTICSEARCH_URL=${elasticsearchHost} " +
                                         "-e TEST_DATABASE_URL=${databaseUrl}") {
                // Test dependencies
                sh 'apk add --no-cache build-base libffi-dev postgresql-dev python3-dev'
                sh 'apk add --no-cache python-dev' // while we continue to run tests under Python 2.7
                sh 'pip3 install -q tox'

                // Unit tests
                sh 'cd /var/lib/hypothesis && tox'
                // Functional tests
                sh 'cd /var/lib/hypothesis && tox -e functional'
                sh 'cd /var/lib/hypothesis && tox -e functional-py3'
            }
        } finally {
            rabbit.stop()
            elasticsearch.stop()
            elasticsearch_old.stop()
            postgres.stop()
        }
    }

    onlyOnMaster {
        stage('release') {
            releaseApp(image: img)
        }
    }
}

onlyOnMaster {
    milestone()
    stage('qa deploy') {
        deployApp(image: img, app: 'h', env: 'qa')
    }

    milestone()
    stage('prod deploy') {
        input(message: "Deploy to prod?")
        milestone()
        deployApp(image: img, app: 'h', env: 'prod')
    }
}

def containerPort(container, port) {
    return sh(
        script: "docker port ${container.id} ${port} | cut -d: -f2",
        returnStdout: true
    ).trim()
}
