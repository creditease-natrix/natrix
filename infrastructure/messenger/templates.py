# -*- coding: utf-8 -*-
from __future__ import unicode_literals


# 邮件模板包含： title(标题) time(当前时间) body(主体内容) supplement(补充内容)
HTML_TEMPLATE = u'''
<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<title>{{title}}</title>
<style type="text/css">.topic_title{line-height:1.6;color:#fff;text-align:center;}
.table_title{font-size:12px;font-weight:normal;color:#222;text-align:left;border-bottom:1px solid #e9e9e9;padding:0px 0 10px;}
.table_cell{font-size:12px;color:#222;padding:10px 0 0;vertical-align:top;text-align:left;}
.help_front{font-size:13px;color:#fff;}
</style>
</head>
<body><div style="width:900px;margin:0 auto;position:relative;">
<table width="100%" cellspacing="0" border="0" cellpadding="0"><tr><td style="position:relative;">
<table width="100%" cellspacing="0" border="0" cellpadding="0" style="background:#3cbde5;">
<tr><td height="18"></td></tr>
<tr><td class="topic_title" style="font-size:24px;">{{title}}</td></tr>
<tr><td class="topic_title" style="font-size:14px;">{{time}}</td></tr>
<tr><td height="20"></td></tr>
</table></td></tr>
<tr><td style="background:#f8f8f8;">
<table width="100%" cellspacing="0" border="0" cellpadding="0">
<tr><td width="20"></td><td>
<table width="100%" cellspacing="0" border="0" cellpadding="0">
<tr><td>
<table width="100%" cellspacing="0" border="0" cellpadding="0">
<tr>
<td height="20"></td>
</tr>
<tr>
<td width="10"></td>
<td width="730">
<table width="100%" cellspacing="0" border="0" cellpadding="0">
<tr>
<td style="font-size:16px;line-height:2.3;color:#333;">你好：</td>
</tr>
<tr>
<td style="font-size:14px;line-height:1.5;color:#333;">
{{body}}
</td>
</tr>
</table>
</td>
</tr>
</table>
</td>
</tr>

<!-- supplementary information: tr -->
<tr>
{{ supplement }}
</tr>
<tr><td height="5"></td></tr>

<!-- footer start -->
<tr>
<td style="background:#3cbde5;position:relative;">
<table width="100%" cellspacing="0" border="0" cellpadding="0">
<tr>
<td width="20"></td>
<td>
<table width="100%" cellspacing="0" border="0" cellpadding="0" >
<tr>
<td class="help_front" style="text-align:center;line-height:3;"><span style="font-size:22px;">你好</span>,如果您在使用过程中遇到问题，欢迎向我们咨询！</td>
</tr>
<tr>
<td>
<table width="100%" cellspacing="0" border="0" cellpadding="0">
<tr>
<td width="570">
<table width="100%" cellspacing="0" border="0" cellpadding="0">
<tr>
<td width="82" class="help_front">官网平台：</td>
<td width="">
<table cellspacing="0" border="0" cellpadding="5">
<tr>
	<td><a href="" class="help_front" style="text-decoration:none;"></a></td>
</tr>
</table>
</td>
</tr>
<tr>
<td width="82" class="help_front" >IM联系：</td>
<td>
<table cellspacing="0" border="0" cellpadding="5">
<tr>
<td class="help_front"></td>
</tr>
</table>
</td>
</tr>
</table>
</td>
</tr>
</table>
</td>
</tr>
<th>
<td height="20"></td>
</th>
</table>
</td>
<td width="20"></td>
</tr>
</table>
</td>
</tr>
<!-- footer end -->
</table></div></body></html>
'''

