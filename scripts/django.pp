stage { 'pre': before => Stage['main'] }            

class python_config {
  class {'epel': } ->
  class { 'python' :
    version    => 'system',
    pip        => true,
    dev        => true,
  } ->
  # Hack because pip provider looks for pip-python instead of the 'pip' command for RH distro's
  file {'/usr/bin/pip-python':
    ensure      => 'link',
    target      => '/bin/pip'
  }                    
}                    

class { 'python_config': stage => 'pre' }

package {'Django':
  ensure      => '1.7.6',
  provider	  => 'pip',
}

class {'apache': }
class {'mysql::server': }
