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
                                         "-e TEST_DATABASE_URL=${databaseUrl} " +
                                         "-e SITE_PACKAGES=true"
                                         ) {
                // Test dependencies
                sh 'apk add --no-cache build-base libffi-dev postgresql-dev python3-dev'
                sh 'apk add --no-cache python-dev' // while we continue to run tests under Python 2.7
                sh 'pip3 install -q tox>=3.8.0'

                // Unit tests
                sh 'cd /var/lib/hypothesis && tox'
                // Functional tests
                sh 'cd /var/lib/hypothesis && tox -e py27-functests'
                sh 'cd /var/lib/hypothesis && tox -e py36-functests'
            }
        } finally {
            rabbit.stop()
            elasticsearch.stop()
            postgres.stop()
            cleanWs()
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
