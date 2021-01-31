if [[ "$OSTYPE" == "linux-gnu"* ]] ; then
	REQUIRED_PKG="python3-tk"
	PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $REQUIRED_PKG|grep "install ok installed")
	echo Checking for $REQUIRED_PKG: $PKG_OK
	if [ "" = "$PKG_OK" ]; then
  		echo "No $REQUIRED_PKG. Setting up $REQUIRED_PKG."
  		sudo apt-get --yes install $REQUIRED_PKG 
	fi
fi

source venv-unix/bin/activate
python3 vorn_finance_tracker.py || python vorn_finance_tracker.py
read -p ""
