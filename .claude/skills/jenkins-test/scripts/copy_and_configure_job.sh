#!/bin/bash
# 复制 Jenkins Job 并配置分支
# 用法: copy_and_configure_job.sh <SKILL_DIR> <SOURCE_JOB> <NEW_JOB> <BRANCH> [--delete-existing]

SKILL_DIR="$1"
SOURCE_JOB="$2"
NEW_JOB="$3"
BRANCH="$4"
DELETE_EXISTING="$5"

jenkins_cli() {
    java -jar "${SKILL_DIR}/lib/jenkins-cli.jar" \
        -s http://10.0.9.238:8080/jenkins/ \
        -auth lianghanguang:11712f96945ee628b3b843842129a84bc2 \
        -http "$@"
}

# 删除已有同名 Job
if [ "$DELETE_EXISTING" = "--delete-existing" ]; then
    jenkins_cli delete-job "$NEW_JOB" 2>/dev/null
fi

# 复制 Job
jenkins_cli copy-job "$SOURCE_JOB" "$NEW_JOB" || { echo "ERROR: 复制 Job 失败"; exit 1; }

# 获取配置
jenkins_cli get-job "$NEW_JOB" > /tmp/jenkins_config.xml || { echo "ERROR: 获取配置失败"; exit 1; }

# 修改分支配置
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('/tmp/jenkins_config.xml')
root = tree.getroot()
for prop in root.iter('hudson.model.ParametersDefinitionProperty'):
    for param in prop.iter('hudson.model.StringParameterDefinition'):
        name_el = param.find('name')
        default_el = param.find('defaultValue')
        if name_el is not None and default_el is not None:
            if name_el.text in ('GIT_BRANCH', 'UPLOAD_BRANCH'):
                default_el.text = '$BRANCH'
tree.write('/tmp/jenkins_config_modified.xml', encoding='unicode', xml_declaration=True)
" || { echo "ERROR: 修改配置失败"; exit 1; }

# 更新配置
jenkins_cli update-job "$NEW_JOB" < /tmp/jenkins_config_modified.xml || { echo "ERROR: 更新配置失败"; exit 1; }

# 启用 Job
jenkins_cli enable-job "$NEW_JOB"

# 输出 URL
ENCODED_JOB=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$NEW_JOB'))")
echo "JOB_URL: http://10.0.9.238:8080/jenkins/job/${ENCODED_JOB}/"
echo "CONSOLE_URL: http://10.0.9.238:8080/jenkins/job/${ENCODED_JOB}/lastBuild/console"
echo "SUCCESS"
