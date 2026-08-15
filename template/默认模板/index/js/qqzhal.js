var i = 0
var end = pages.length
while(i != end)
{
	document.write("<tr>")
	for(nn = 1;nn < 5;nn++)
	{
		if (i == end)
		{
			if(nn == 1) break;
			else document.write("<td class='tablebody1' align='middle' style='width:25%;height:30'>&nbsp;</td>");
		}
		else
		{
			if (pages[i][3] != undefined)
			{
				if(nn == 1)
				{
					if(pages[i][3].substr(0,4) == "<img")
					{
						document.write("<td colspan=1 align=center>"+pages[i][3]+"</td><td class='tablebody1' colspan=3>"+pages[i][1]+"</td>");
						nn = 5;
						i++;
					}
					else
					{
						document.write("<td class='tablebody2' colspan='4' align='center' valign='middle' style='height:30'><a href=javascript:loadurl('volume.htm',"+i+") title='分卷阅读'>"+pages[i][3]+"</a></td>");
						document.write("</tr><tr>");
						document.write("<td class='tablebody1' valign='middle' style='width:25%;height:30'>");
						document.write("<a href=javascript:loadurl('chapter.htm',"+i+") title='本章字数："+pages[i][2]+"'>"+pages[i][1]+"</a>");
						document.write("</td>");
						i++;
					}
				}
				else document.write("<td class='tablebody1' align='middle' style='width:25%;height:30'>&nbsp;</td>");
			}
			else
			{
				document.write("<td class='tablebody1' valign='middle' style='width:25%;height:30'>");
				document.write("<a href=javascript:loadurl('chapter.htm',"+i+") title='本章字数："+pages[i][2]+"'>"+pages[i][1]+"</a>");
				document.write("</td>");
				i++;
			}
		}
	}
	document.write("</tr>");
}
function gotoNextPage()
{
    	if (window.event.keyCode == 39 && parent.txt != undefined) loadurl("chapter.htm",parent.txt);
}
document.onkeydown = gotoNextPage;