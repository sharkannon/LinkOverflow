stage { 'pre': before => Stage['main'] }

# Python/Django install/config class for LinkOverflow project
class python_config {
  class {'epel': } ->
  class { 'python' :
    version    => 'system',
    pip        => true,
    dev        => true,
    virtualenv => false,
  } ->
  
  # Hack because pip provider looks for pip-python instead of the 'pip' command for RH distro's
  file {'/usr/bin/pip-python':
    ensure => 'link',
    target => '/bin/pip'
  }
}

class { 'python_config': stage => 'pre' }

package {'Django':
  ensure   => '1.7.6',
  provider => 'pip',
}

class { 'apache':
  default_mods        => false,
  default_confd_files => false,
}

class {'apache::mod::wsgi':
        wsgi_python_path   => '/var/www/mysite',
}

apache::vhost { 'wsgi.example.com':
  default_vhost               => true,
  port                        => '80',
  docroot                     => '/var/www',
  wsgi_script_aliases         => { '/' => '/var/www/mysite/mysite/wsgi.py' },
}

firewall { '100 allow http and https access':
  port   => [80, 443],
  proto  => tcp,
  action => accept,
}