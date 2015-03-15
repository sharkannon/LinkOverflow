stage { "pre": before => Stage["main"] }            

class python {
  package {'python': 
    ensure      => '2.7.5-16.el7',
  } ->
  
  package {'python-setuptools':
    ensure      => 'latest',
  }

  exec { "easy_install pip":                
    path        => "/usr/local/bin:/usr/bin:/bin",
    require     => Package["python-setuptools"],
    subscribe   => Package["python-setuptools"],        
  } ->
  file {'/usr/bin/pip-python':
    ensure      => 'link',
    target      => '/bin/pip'
  }                    
}                    

class { "python": stage => "pre" }

package {'Django':
  ensure      => '1.7.6',
  provider	  => 'pip',
}
