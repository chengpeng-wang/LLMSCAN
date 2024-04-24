import re


def parse_bug_report(output):
    begin_marker = "BEGIN REPORT"
    end_marker = "END REPORT"

    lines = output.split("\n")
    start_parsing = False

    report_lines = []

    for line in lines:
        line = line.strip()

        if begin_marker in line:
            start_parsing = True
            continue

        if end_marker in line:
            break

        if start_parsing:
            report_lines.append(line)

    bug_num = None
    explanations = []
    traces = []

    if len(report_lines) > 0:
        if len(report_lines[0].split()) > 3:
            if report_lines[0].split()[2].isdigit():
                bug_num = int(report_lines[0].split()[2])

    for line in report_lines:
        if line.startswith("- "):
            if not ("[Explanation" in line and "]" in line and "[Trace" in line):
                continue
            bug_trace = line[line.find("[Trace:") + 7 : -1].strip()
            trace = []
            # Use regular expression to find and extract line numbers and data
            for item in bug_trace.replace("(Line ", "(")[1:-1].split("), ("):
                line_number_str = item[:item.find(", ")]
                var_name_str = item[item.find(", ") + 2:]
                if len(var_name_str) <= 2:
                    continue
                var_name_str = item[item.find(", ") + 2:][:-1]
                if "is_null" in var_name_str:
                    var_name_str = var_name_str.replace("is_null", "")
                elif "is_zero" in var_name_str:
                    var_name_str = var_name_str.replace("is_zero", "")
                elif "is_sensitive" in var_name_str:
                    var_name_str = var_name_str.replace("is_sensitive", "")
                else:
                    continue
                var_name_str = var_name_str[1:]
                if line_number_str.isdigit():
                    trace.append((int(line_number_str), var_name_str))
            traces.append(trace)
    return bug_num, traces, "\n".join(report_lines)


if __name__ == "__main__":
    output = """
    -------------BEGIN REPORT----------------
    There are 2 xss bugs in the program:
    - Bug 1: [Explanation: In the file CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java, the value of data at line 54 is produced by the return value of readLine. It is then passed to the function CWE80_XSS__CWE182_Servlet_connect_tcp_53b_hooSink at line 102, making it sensitive. The parameter data is used as the parameter of println at line 154, which causes an XSS bug at line 154.], [Trace: (Line 54, CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java), (Line 102, CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java), (Line 154, CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java)]
    - Bug 2: [Explanation: In the file CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java, the value of data at line 116 is a constant string "foo", which is not sensitive. However, it is passed to the function CWE80_XSS__CWE182_Servlet_connect_tcp_53b_fooxxSink at line 118, making it sensitive. The parameter data is used as the parameter of println at line 163, which causes an XSS bug at line 163.], [Trace: (Line 116, CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java), (Line 118, CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java), (Line 163, CWE80_XSS__CWE182_Servlet_connect_tcp_53a.java)]
    ---------------END REPORT----------------
    """
    bug_num, traces, report = parse_bug_report(output)
    print(traces)
