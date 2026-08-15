//Ë«»÷¹öÆÁ
var currentpos, timer;
function initialize(){
  timer = setInterval("scrollwindow()", 50);
}
function sc(){
  clearInterval(timer);
}
function scrollwindow(){
  currentpos = document.body.scrollTop;
  window.scroll(0, ++currentpos);
  if (currentpos != document.body.scrollTop)
    sc();
}

document.onmousedown = sc
document.ondblclick = initialize

var dsize=14;

function reduce()
{
dsize--;
txt.style.cssText='{font-size:'+dsize+'pt;}';
txt.style.color=txtcolor.options[txtcolor.selectedIndex].value;
parent.FontSize=dsize;
}

function enlarge()
{
dsize++;
txt.style.cssText='{font-size:'+dsize+'pt;}';
txt.style.color=txtcolor.options[txtcolor.selectedIndex].value;
parent.FontSize=dsize;
}

function loadchapter()
{
	bcolor.selectedIndex = parent.bcolor1;
	txtcolor.selectedIndex = parent.txtcolor1;
	bkk.style.background=bcolor.options[bcolor.selectedIndex].value;	
	txt.style.color=txtcolor.options[txtcolor.selectedIndex].value;
if(parent.FontSize!=null)
{
var pat=/[0-9]+/gi;
if(pat.exec(parent.FontSize))
{
dsize=parent.FontSize;
txt.style.cssText='{font-size:'+dsize+'pt;}';
txt.style.color=txtcolor.options[txtcolor.selectedIndex].value;
}
}
}

