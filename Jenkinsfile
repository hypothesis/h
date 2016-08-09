#!groovy

node {
    stage 'Build'
    checkout scm

    // Store the short commit id for use tagging images
    sh 'git rev-parse --short HEAD > GIT_SHA'
    gitSha = readFile('GIT_SHA').trim()

    sh "make docker DOCKER_TAG=${gitSha}"
    img = docker.image "hypothesis/hypothesis:${gitSha}"

    stage 'Test'
    docker.image('postgres:9.4').withRun('-P -e POSTGRES_DB=htest') {c ->
        sh "echo postgresql://postgres@\$(facter ipaddress_eth0):\$(docker port ${c.id} 5432 | cut -d: -f2)/htest > DATABASE_URL"
        databaseUrl = readFile('DATABASE_URL').trim()

        // Run our Python tests inside the built container
        img.inside("-u root -e TEST_DATABASE_URL=${databaseUrl}") {
            // Test dependencies
            sh 'apk-install build-base libffi-dev postgresql-dev python-dev'
            sh 'pip install -q tox'

            // Unit tests
            sh 'cd /var/lib/hypothesis && tox'
        }
    }

    // We only push the image to the Docker Hub if we're on master
    if (env.BRANCH_NAME != 'master') {
        return
    }
    stage 'Push'
    docker.withRegistry('', 'docker-hub-build') {
        img.push('auto')
    }
}
