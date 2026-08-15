var prevpage=0;var nextpage=0;var end=pages.length;
for(prevpage=parent.txt-1;prevpage>-2;prevpage--){
	if(prevpage==-1){break}
	if(pages[prevpage][3]!=undefined&&pages[prevpage][3].substr(0,1)!="<"){break}
}

for(nextpage=parent.txt+1;nextpage<end+1;nextpage++){
	if(nextpage==end){break}
	if(pages[nextpage][3]!=undefined&&pages[nextpage][3].substr(0,1)!="<"){break}
}

function next(a,b,c,j){
	var s="";
	if(prevpage!=-1&&a!="")
		document.write("<A href=javascript:loadurl('volume.htm',prevpage)>"+a+"</A>");
	if(j>0)
		for(i=1;i<=j;i++)s=s+"&nbsp;";
	if(b!="")
		document.write(s+"<a href=index.htm>"+b+"</A>"+s);
	if(nextpage!=end&&c!="")
		document.write("<A href=javascript:loadurl('volume.htm',nextpage)>"+c+"</A>");
}

function gotoNextPage(){
	if(window.event.keyCode==13)
		document.location='index.htm';
	if(window.event.keyCode==37&&prevpage!=-1)
		loadurl('volume.htm',prevpage);
	if(window.event.keyCode==39&&nextpage!=end)
		loadurl('volume.htm',nextpage);
	if(window.event.keyCode==116){
		event.keyCode=0;event.returnValue=false
	};
}

document.onkeydown=gotoNextPage;next("<img src='images/previousj.gif' width=61 height=19 border=0>","<img src='images/return.gif' width=85 height=19 border=0>","<img src='images/nextj.gif' width=61 height=19 border=0>",2);