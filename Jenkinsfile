#!groovy

@Library('pipeline-library') _

def image
def ws_only_image

node {
    stage('build') {
        checkout(scm)
        image = buildApp(name: 'hypothesis/hypothesis')
        ws_only_image = buildApp(name: 'hypothesis/hypothesis-ws', path: 'h/streamer')
    }

    stage('test') {
        hostIp = sh(script: 'facter ipaddress_eth0', returnStdout: true).trim()

        postgres = docker.image('postgres:11.5').run('-P -e POSTGRES_DB=htest')
        databaseUrl = "postgresql://postgres@${hostIp}:${containerPort(postgres, 5432)}/htest"

        elasticsearch = docker.image('hypothesis/elasticsearch').run('-P -e "discovery.type=single-node"')
        elasticsearchHost = "http://${hostIp}:${containerPort(elasticsearch, 9200)}"

        rabbit = docker.image('rabbitmq').run('-P')
        brokerUrl = "amqp://guest:guest@${hostIp}:${containerPort(rabbit, 5672)}//"

        try {
            testApp(image: image, runArgs: "-u root " +
                                         "-e BROKER_URL=${brokerUrl} " +
                                         "-e ELASTICSEARCH_URL=${elasticsearchHost} " +
                                         "-e TEST_DATABASE_URL=${databaseUrl} " +
                                         "-e SITE_PACKAGES=true"
                                         ) {
                // Test dependencies
                sh 'apk add --no-cache build-base libffi-dev postgresql-dev'
                sh 'apk add --no-cache python3 python3-dev'
                sh 'pip install -q tox>=3.8.0'

                // Functional tests
                sh 'cd /var/lib/hypothesis && tox -e functests'
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
            releaseApp(image: image)
            releaseApp(image: ws_only_image)
        }
    }
}

onlyOnMaster {
    milestone()
    stage('qa deploy') {
        deployApp(image: image, app: 'h', env: 'qa', region: "us-west-1")
    }

    milestone()
    stage("approval") {
        input(message: "Proceed to production deploy?")
    }

    milestone()
    stage("prod Deploy") {
        parallel(
            us: {
                deployApp(image: image, app: "h", env: "prod", region: "us-west-1")
            },
            ca: {
		// Workaround to ensure all parallel builds happen. See https://hypothes-is.slack.com/archives/CR3E3S7K8/p1625041642057400
                sleep 2
                deployApp(image: image, app: "h-ca", env: "prod", region: "ca-central-1")
            }
        )
    }
}

def containerPort(container, port) {
    return sh(
        script: "docker port ${container.id} ${port} | cut -d: -f2",
        returnStdout: true
    ).trim()
}
