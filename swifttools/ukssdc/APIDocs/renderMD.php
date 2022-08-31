<?php 
  require_once (getenv("SWIFT_CONFIG")."/swift.php");
  require_once ( SWIFT_CONFIG."/AutoprocPaths.php");
  require_once ( SWIFT_PAGE."/page.php");	
  require_once ( SWIFT_PAGE."/sidebar.php");	
  require_once( SWIFT_FUNC."/Parsedown.php");
  require_once( SWIFT_FUNC."/ParsedownExtra.php");

  if (!isset($_GET["infile"]))
    do404(1);
  $file=$_GET["infile"];

  $dir = str_replace("$API_PATH/APIDocs/", "", $file);
  $dir = str_replace("/README", "", $file);
  

  
  $file=$file.".md";
  
  if (!is_file($file))
    do404();

  
  
  $page=new Page("", $_GET, "Phil Evans", "2022 August 17");
  $page->setStyle("/style/markdown.css");
  $head=$page->Head();
  $head->Title("UKSSDC | Swifttools API documentation | $file");
  $head->Description("Documentation supporting the swifttools Python module");
  $head->Keywords("Swift, XRT,Python, API, swifttools");

  $head->Append(
  "
    <script src='/scripts/highlight.pack.js'></script>
    <script>hljs.initHighlightingOnLoad();</script>
  "
  );

  $hasSB=0;
  $bread = "API";
  
  
  
  $page->Begin(); 
  print "<p id='breadcrumb'><a href='$URLBASE' title='UKSSDC home'>Home</a> &gt; <a href='/access'>Data Access</a> &gt; "
        ."<a href='/API'>API access</a> &gt; ";
  
  $levels = explode("/", $dir);
  $build="";
  $dirs="";
  if (!is_null($levels))
  {
    for ($i=0; $i<count($levels)-1; $i++)
    {
      $link = "/API/$dirs$levels[$i]";
      if ($i>0 && ($i == count($levels)-2) )
        $link.=".md";
      print "<a href='$link'>swifttools.$build$levels[$i]</a> &gt;";
      $build.="$levels[$i].";
      $dirs.="$levels[$i]/";
    }
  }
  $last = $levels[count($levels)-1];
  print "swifttools.$build$last</p>\n";

  $Parsedown = new ParsedownExtra();
  print "<div id='markDownHolder'>\n";
  $txt= $Parsedown->text(file_get_contents($file));
  $txt = str_replace("<hr />", "<hr class='heavy'/>", $txt);
  print $txt;
  print "</div>\n";
  $page->End();
