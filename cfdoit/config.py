
import yaml

class Config :

  config = {}

  def print() :
    print(yaml.dump(Config.config))