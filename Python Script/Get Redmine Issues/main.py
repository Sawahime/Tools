import requests
from datetime import datetime


class RedmineClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def get_issues(self, limit=100, offset=0):
        """
        获取issues数据，支持分页
        """
        url = f"{self.base_url}/issues.json"
        params = {
            'limit': limit,
            'offset': offset
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            return None

    def get_issues_by_assignee(self, assignee_name, limit=100, offset=0):
        """
        根据分配人员筛选issues
        """
        url = f"{self.base_url}/issues.json"
        params = {
            'limit': limit,
            'offset': offset,
            'assigned_to_id': '*'  # 获取所有分配的任务
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # 筛选指定分配人员的issues
            filtered_issues = []
            for issue in data.get('issues', []):
                assigned_to = issue.get('assigned_to', {})
                if assigned_to and assigned_to.get('name') == assignee_name:
                    filtered_issues.append(issue)

            # 构建返回数据格式
            return {
                'issues': filtered_issues,
                'total_count': len(filtered_issues),
                'offset': offset,
                'limit': limit
            }

        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            return None

    def get_issues_as_dict_by_assignee(self, assignee_name, limit=100, offset=0):
        """
        根据分配人员获取IssueInfo对象列表
        """
        issues_data = self.get_issues_by_assignee(assignee_name, limit, offset)
        if not issues_data:
            return []

        issues_dict = []
        for issue in issues_data.get('issues', []):
            # 处理分配人员
            assigned_to = issue.get('assigned_to', {})
            assigned_to_name = assigned_to.get('name') if assigned_to else None

            # 处理项目
            project = issue.get('project', {})
            project_name = project.get('name', 'N/A')

            # 处理跟踪类型
            tracker = issue.get('tracker', {})
            tracker_name = tracker.get('name', 'N/A')

            issue_dict = {
                'id': issue.get('id', 0),
                'subject': issue.get('subject', 'N/A'),
                'status': issue.get('status', {}).get('name', 'N/A'),
                'priority': issue.get('priority', {}).get('name', 'N/A'),
                'author': issue.get('author', {}).get('name', 'N/A'),
                'assigned_to': assigned_to_name,
                'created_on': self.format_date(issue.get('created_on', 'N/A')),
                'updated_on': self.format_date(issue.get('updated_on', 'N/A')),
                'start_date': issue.get('start_date'),
                'due_date': issue.get('due_date'),
                'done_ratio': issue.get('done_ratio', 0),
                'project': project_name,
                'tracker': tracker_name,
                'description': issue.get('description', '')
            }
            issues_dict.append(issue_dict)

        return issues_dict

    def display_issues(self, issues_data):
        """
        格式化显示issues数据
        """
        if not issues_data:
            print("没有获取到数据")
            return

        issues = issues_data.get('issues', [])
        total_count = issues_data.get('total_count', 0)
        offset = issues_data.get('offset', 0)
        limit = issues_data.get('limit', 0)

        print("=" * 100)
        print(f"Redmine Issues (显示 {len(issues)}/{total_count} 个)")
        print("=" * 100)

        for i, issue in enumerate(issues, 1):
            self.print_issue(issue, i + offset)

    def print_issue(self, issue, number):
        """
        打印单个issue的详细信息
        """
        print(f"\n{number}. 问题 #{issue.get('id', 'N/A')}")
        print(f"   📌 主题: {issue.get('subject', 'N/A')}")
        print(f"   📊 状态: {issue.get('status', {}).get('name', 'N/A')}")
        print(f"   ⚡ 优先级: {issue.get('priority', {}).get('name', 'N/A')}")
        print(f"   👤 作者: {issue.get('author', {}).get('name', 'N/A')}")

        # 分配人员（如果有）
        assigned_to = issue.get('assigned_to', {})
        if assigned_to:
            print(f"   ✅ 分配给: {assigned_to.get('name', 'N/A')}")

        print(f"   📅 创建时间: {self.format_date(issue.get('created_on', 'N/A'))}")
        print(f"   🔄 更新时间: {self.format_date(issue.get('updated_on', 'N/A'))}")

        # 计划开始时间和结束时间
        start_date = issue.get('start_date', '')
        if start_date:
            print(f"   🗓️  计划开始: {start_date}")

        due_date = issue.get('due_date', '')
        if due_date:
            print(f"   📋 计划完成: {due_date}")

        # 进度（完成百分比）
        done_ratio = issue.get('done_ratio', 0)
        print(f"   📈 进度: {done_ratio}%")

        # 项目信息
        project = issue.get('project', {})
        if project:
            print(f"   📁 项目: {project.get('name', 'N/A')}")

        # 跟踪类型
        tracker = issue.get('tracker', {})
        if tracker:
            print(f"   🏷️  类型: {tracker.get('name', 'N/A')}")

        # 描述信息
        description = issue.get('description', '')
        if description:
            desc_preview = description[:150] + "..." if len(description) > 150 else description
            print(f"   📝 描述: {desc_preview}")

        print("-" * 80)

    def format_date(self, date_string):
        """
        格式化日期字符串
        """
        if date_string == 'N/A':
            return 'N/A'

        try:
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return date_string


def main():
    """
    主函数
    """
    # 配置Redmine服务器地址
    redmine_url = "http://192.168.3.202:3000"

    # 创建Redmine客户端
    client = RedmineClient(redmine_url)

    print("🔍 正在从Redmine服务器获取issues数据...")
    issues_data = client.get_issues_by_assignee(assignee_name="毅 陆")

    if issues_data:
        client.display_issues(issues_data)
    else:
        print("❌ 获取数据失败，请检查：")
        print("   1. Redmine服务器是否运行")
        print("   2. 网络连接是否正常")
        print("   3. 服务器地址是否正确")


def get_issues_cpp_intf():
    redmine_url = "http://192.168.3.202:3000"
    client = RedmineClient(redmine_url)
    return client.get_issues_as_dict_by_assignee(assignee_name="毅 陆")


def test():
    issues = get_issues_cpp_intf()

    print(f"🔍 分配给【毅 陆】的issues (总计: {len(issues)} 个)")
    print("=" * 100)

    # 打印每个issue的详细信息
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. 问题 #{issue['id']}")
        print(f"   📌 主题: {issue['subject']}")
        print(f"   📊 状态: {issue['status']}")
        print(f"   ⚡ 优先级: {issue['priority']}")
        print(f"   👤 作者: {issue['author']}")
        print(f"   ✅ 分配给: {issue['assigned_to'] or '未分配'}")
        print(f"   📈 进度: {issue['done_ratio']}%")
        print(f"   📅 创建时间: {issue['created_on']}")
        print(f"   🔄 更新时间: {issue['updated_on']}")

        if issue['start_date']:
            print(f"   🗓️  计划开始: {issue['start_date']}")
        if issue['due_date']:
            print(f"   📋 计划完成: {issue['due_date']}")

        print(f"   📁 项目: {issue['project']}")
        print(f"   🏷️  类型: {issue['tracker']}")

        if issue['description']:
            desc_preview = issue['description'][:150] + \
                "..." if len(issue['description']) > 150 else issue['description']
            print(f"   📝 描述: {desc_preview}")

        print("-" * 80)


if __name__ == "__main__":
    # main()
    test()
