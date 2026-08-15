var currentpos,timer,speed;

function initialize(){
	timer=setInterval("scrollwindow()",speed);
}

function sc(){
	clearInterval(timer);
}

function scrollwindow(){
	currentpos=document.body.scrollTop;
	window.scroll(0,++currentpos);
	if(currentpos!=document.body.scrollTop)
		sc();
}

document.onmousedown=sc;
document.ondblclick=initialize;

var dsize=18;

function reduce(){
	if(dsize>1){
		dsize--;txt.style.fontSize=+dsize+'pt';
		parent.zihao=dsize;
	}
}

function enlarge(){
	dsize++;
	txt.style.fontSize=+dsize+'pt';
	parent.zihao=dsize;
}

function loadchapter(){
	gunsu.selectedIndex=parent.gunsu;
	speed=gunsu.options[gunsu.selectedIndex].value;
	beijing.selectedIndex=parent.beijing;
	bkk.style.cssText=beijing.options[beijing.selectedIndex].value;
	haju.selectedIndex=parent.haju;
	txt.style.lineHeight=haju.options[haju.selectedIndex].value;
	kuan.selectedIndex=parent.kuan;
	txt.style.width=kuan.options[kuan.selectedIndex].value;
	cuxi.selectedIndex=parent.cuxi;
	txt.style.fontWeight=cuxi.options[cuxi.selectedIndex].value;
	ziti.selectedIndex=parent.ziti;
	txt.style.fontFamily=ziti.options[ziti.selectedIndex].value;
	zise.selectedIndex=parent.zise;txt.style.color=zise.options[zise.selectedIndex].value;
	var pat=/[0-9]+/gi;
	if(pat.exec(parent.zihao)){
		dsize=parent.zihao;
		txt.style.fontSize=+dsize+'pt';
	}
}

var key=new Array();
key[',']="javascript:reduce()";
key['.']="javascript:enlarge()";


function getKey(keyStroke){
	isNetscape=(document.layers);
	eventChooser=(isNetscape)?keyStroke.which:event.keyCode;
	which=String.fromCharCode(eventChooser).toLowerCase();
	for(var i in key)
		if(which==i)
			window.location=key[i];
}
document.onkeypress=getKey;


function setCookies(cookieName,cookieValue,expirehours){
	var today=new Date();
	var expire=new Date();
	expire.setTime(today.getTime()+3600000*356*24);
	document.cookie=cookieName+'='+escape(cookieValue)+';expires='+expire.toGMTString();
}

function ReadCookies(cookieName){
	var theCookie=''+document.cookie;
	var ind=theCookie.indexOf(cookieName);
	if(ind==-1||cookieName=='')
		return'';
	var ind1=theCookie.indexOf(';',ind);
	if(ind1==-1)
		ind1=theCookie.length;
	return unescape(theCookie.substring(ind+cookieName.length+1,ind1));
}

function saveSet(){
	setCookies("shizi",shizi.options[shizi.selectedIndex].value);
	setCookies("gunsu",gunsu.options[gunsu.selectedIndex].value);
	setCookies("beijing",beijing.options[beijing.selectedIndex].value);
	setCookies("haju",haju.options[haju.selectedIndex].value);
	setCookies("kuan",kuan.options[kuan.selectedIndex].value);
	setCookies("ziti",ziti.options[ziti.selectedIndex].value);
	setCookies("zise",zise.options[zise.selectedIndex].value);
	setCookies("dsize",dsize);
}

function loadSet(){
	var tmpstr;
	tmpstr=ReadCookies("shizi");
	shizi.selectedIndex=0;
	if(tmpstr!=""){
		for(var i=0;i<shizi.length;i++){
			if(shizi.options[i].value==tmpstr){
				shizi.selectedIndex=i;
				break
			}
		}
	}
	tmpstr=ReadCookies("gunsu");
	gunsu.selectedIndex=0;
	
	if(tmpstr!=""){
		for(var i=0;i<gunsu.length;i++){
			if(gunsu.options[i].value==tmpstr){
				gunsu.selectedIndex=i;
				break;
			}
		}
	}
	
	tmpstr=ReadCookies("beijing");
	beijing.selectedIndex=0;
	if(tmpstr!=""){
		for(var i=0;i<beijing.length;i++){
			if(beijing.options[i].value==tmpstr){
				beijing.selectedIndex=i;
				break;
			}
		}
	}
	tmpstr=ReadCookies("haju");
	haju.selectedIndex=0;
	if(tmpstr!=""){
		for(var i=0;i<haju.length;i++){
			if(haju.options[i].value==tmpstr){
				haju.selectedIndex=i;
				break;
			}
		}
	}
	
	tmpstr=ReadCookies("kuan");
	kuan.selectedIndex=0;
	if(tmpstr!=""){
		for(var i=0;i<kuan.length;i++){
			if(kuan.options[i].value==tmpstr){
				kuan.selectedIndex=i;
				break;
			}
		}
	}
	
	tmpstr=ReadCookies("ziti");
	ziti.selectedIndex=0;
	if(tmpstr!=""){
		for(var i=0;i<ziti.length;i++){
			if(ziti.options[i].value==tmpstr){
				ziti.selectedIndex=i;
				break
			}
		}
	}
	
	tmpstr=ReadCookies("zise");
	zise.selectedIndex=0;
	if(tmpstr!=""){
		for(var i=0;i<zise.length;i++){
			if(zise.options[i].value==tmpstr){
				zise.selectedIndex=i;
				break;
			}
		}
	}
	
	tmpstr=ReadCookies("dsize");
	if(tmpstr=='')tmpstr=12;
	var pat=/[0-9]+/gi;
	
	if(pat.exec(tmpstr)){
		dsize=tmpstr;
		txt.style.fontSize=+dsize+'pt';
	}
	
	float.style.visibility=shizi.options[shizi.selectedIndex].value;
	speed=gunsu.options[gunsu.selectedIndex].value;
	bkk.style.cssText=beijing.options[beijing.selectedIndex].value;
	txt.style.lineHeight=haju.options[haju.selectedIndex].value;
	txt.style.width=kuan.options[kuan.selectedIndex].value;
	txt.style.fontFamily=ziti.options[ziti.selectedIndex].value;
	txt.style.color=zise.options[zise.selectedIndex].value;
}