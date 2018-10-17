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
                sh 'apk add --no-cache build-base libffi-dev postgresql-dev python-dev'
                sh 'apk add --no-cache python3 python3-dev'
                sh 'pip install -q tox tox-pip-extensions'

                // Unit tests
                sh 'cd /var/lib/hypothesis && tox'
                // Functional tests
                sh 'cd /var/lib/hypothesis && tox -e functional'
                sh 'cd /var/lib/hypothesis && tox -e functional-py36'
            }
        } finally {
            rabbit.stop()
            elasticsearch.stop()
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
