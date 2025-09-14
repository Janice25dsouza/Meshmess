use std::error::Error;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Starting Windows BLE advertiser...");

    let payload = "NodeA".to_string(); // Try a shorter name

    advertise(payload).await?;

    Ok(())
}

#[cfg(target_os = "windows")]
async fn advertise(payload: String) -> Result<(), Box<dyn Error>> {
    use windows::Devices::Bluetooth::Advertisement::{
        BluetoothLEAdvertisement, BluetoothLEAdvertisementPublisher,
        BluetoothLEAdvertisementPublisherStatusChangedEventArgs,
    };
    use windows::Foundation::TypedEventHandler;
    use windows::core::HSTRING;

    println!("Running Windows advertiser...");

    let adv = BluetoothLEAdvertisement::new()?;
    let local_name = HSTRING::from(payload.clone());
    adv.SetLocalName(&local_name)?;

    let publisher = BluetoothLEAdvertisementPublisher::new()?;

    // Access Advertisement and configure it
    let advertisement = publisher.Advertisement()?;
    advertisement.SetLocalName(&local_name)?;

    let handler = TypedEventHandler::new(
        |_pub: &Option<BluetoothLEAdvertisementPublisher>,
         args: &Option<BluetoothLEAdvertisementPublisherStatusChangedEventArgs>| {
            if let Some(a) = args {
                println!("Publisher status changed: {:?}", a.Status().unwrap());
            }
            Ok(())
        },
    );

    publisher.StatusChanged(&handler)?;

    // Start advertising only after everything is set
    publisher.Start()?;
    println!("Advertising with name: {}", payload);

    loop {
        sleep(Duration::from_secs(5)).await;
    }
}

#[cfg(not(target_os = "windows"))]
async fn advertise(_payload: String) -> Result<(), Box<dyn Error>> {
    println!("Unsupported platform for advertising.");
    Ok(())
}
