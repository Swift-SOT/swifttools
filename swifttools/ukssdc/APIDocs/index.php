<?php  
  require_once (getenv("SWIFT_CONFIG")."/swift.php");
  require_once ( SWIFT_CONFIG."/AutoprocPaths.php");
  require_once ( SWIFT_PAGE."/page.php");
  
  $page=new Page("", $_GET, "Phil Evans", "2022 August 12");
  $page->setStyle("/style/LSXPS_docs.css");
  $head=$page->Head();
  $head->Title("UKSSDC | Swifttools API");
  $head->Description("Documentation supporting the swifttools API"); 
  $head->Keywords("Swift, GRB, XRT, light curve, documentation, API, swifttools");
  $head->AddScriptRef("/scripts/centre.js");
  $head->AddScriptRef("/scripts/jquery.min.js");
  $head->AddScriptRef("/scripts/jquery_scrollto.js");
  $head->AddScriptRef("/scripts/autoproc_base.js");
  $head->AddScriptRef("/scripts/jquery-ui.js");
  
  $page->PageFoot()->W3C( True );
  $page->PageFoot()->WAI( 2 );
  $page->Begin(); 
  print "<p id='breadcrumb'><a href='' title='UKSSDC home'>Home</a> &gt; &gt; API Documentation</p>\n";
//   print "<p id='help' class='hidden'><a href='javascript:showGlossary(\"help\");'>Help</a>.</p>\n";
?>
  <h1>The swifttools API</h1>

  <p style='width: 74%; margin: 10px auto; text-align:center; background-color: yellow; border-radius: 15px; border: 1px solid #CC0;'>Version 3.0 of <code>swifttools</code>
  was released on 2022 August 31. This major release introduces the <code>swifttools.ukssdc</code> module.</p>
  
  <p>Various aspects of working with Swift can now be done via the <code>swifttools</code> Python module. This is available through pip:</p>
  
  <pre>
  pip install [--upgrade] swifttools
  </pre>
  
  <p>(The <code>--upgrade</code> is only needed if you have an older version of this module installed).</p>
    
  <p>This module has 2 sub-modules:</p>
  
  <dl title='swifttools components'>
  
    <dt><code>swifttools.swift_too</code> [<a href='https://www.swift.psu.edu/too_api/'>Docs</a>]</dt>
    <dd>This module includes access to Swift data, the ability to query observability of a source,
    get an object's observing history, and submit ToO requests. It is maintained by Jamie Kennea, and is <a href='https://www.swift.psu.edu/too_api/'>fully 
    documented on the PSU web site</a>.</dd>
      
    <dt><code>swifttools.ukssdc</code> [<a href='ukssdc/'>Docs</a>]</dt>
    <dd>This module provides access to Swift data, the <a href='<?php echo $PROD_URL;?>'>XRT GRB products</a>, the
    <a href='<?php echo $LSXPS_URL;?>'>LSXPS catalogue</a>, the <a href='<?php echo $UOB_URL;?>'>on-demand data-analysis tools</a> and more. It is
    maintained by Phil Evans and is <a href='ukssdc/'>fully documented here</a>.</dd>
    
     
  </dl>
   
  <br style='clear:both;'/>
   
  <p>Although we recommend installing via <code>pip</code> the source code is also available via
  a <a href='https://gitlab.com/DrPhilEvans/swifttools'>public GitLab repository</a>, which is also where you
  can report issues / bugs.</p>
   
   
  
<?php 
  $page->End();


