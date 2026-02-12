using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

public class LidarUdpReceiver : MonoBehaviour
{
    [Serializable]
    public class Packet
    {
        public Tfluna tfluna;
        public Bno055 bno055;
    }

    [Serializable]
    public class Tfluna
    {
        public double timestamp;
        public float distance_cm;
        public int strength;
        public float temperature_c;
    }

    [Serializable]
    public class Bno055
    {
        public double timestamp;
        public float qw, qx, qy, qz;
    }

    public int port = 5005;
    public Transform pointPrefab;
    public float scaleMeters = 0.01f;
    public int maxPoints = 5000;
    public bool debugOverlay = true;
    public bool ignoreOrientation = false;

    private UdpClient _client;
    private Thread _thread;
    private bool _running;
    private readonly object _lock = new object();
    private Packet _latest;
    private int _packetCount;
    private long _lastPacketTicks;
    private string _lastSender;

    private Quaternion _calibration = Quaternion.identity;
    private bool _hasCalibration;

    void Start()
    {
        _client = new UdpClient(port);
        _client.Client.ReceiveTimeout = 250;
        _running = true;
        _thread = new Thread(ReceiveLoop) { IsBackground = true };
        _thread.Start();
    }

    void ReceiveLoop()
    {
        var endPoint = new IPEndPoint(IPAddress.Any, port);
        while (_running)
        {
            try
            {
                var data = _client.Receive(ref endPoint);
                var json = Encoding.UTF8.GetString(data);
                var packet = JsonUtility.FromJson<Packet>(json);
                if (packet == null) continue;

                lock (_lock)
                {
                    _latest = packet;
                    _packetCount++;
                    _lastPacketTicks = DateTime.UtcNow.Ticks;
                    _lastSender = endPoint.ToString();
                }
            }
            catch (SocketException)
            {
                // Timeout to allow thread to exit cleanly.
            }
            catch (ObjectDisposedException)
            {
                break;
            }
            catch
            {
            }
        }
    }

    void Update()
    {
        if (IsCalibrationPressed())
        {
            Packet snapshot;
            lock (_lock)
            {
                snapshot = _latest;
            }

            if (snapshot != null && snapshot.bno055 != null)
            {
                var raw = new Quaternion(snapshot.bno055.qx, snapshot.bno055.qy, snapshot.bno055.qz, snapshot.bno055.qw);
                _calibration = Quaternion.Inverse(raw);
                _hasCalibration = true;
            }
        }

        if (pointPrefab == null) return;

        Packet current;
        lock (_lock)
        {
            current = _latest;
        }

        if (current == null) return;

        if (current.tfluna == null || current.bno055 == null) return;

        var q = new Quaternion(current.bno055.qx, current.bno055.qy, current.bno055.qz, current.bno055.qw);
        if (_hasCalibration)
        {
            q = _calibration * q;
        }

        var dir = ignoreOrientation ? Vector3.forward : (q * Vector3.forward);
        var pos = dir * (current.tfluna.distance_cm * scaleMeters);

        var point = Instantiate(pointPrefab, pos, Quaternion.identity);
        point.SetParent(transform, false);

        if (transform.childCount > maxPoints)
        {
            Destroy(transform.GetChild(0).gameObject);
        }
    }

    void OnGUI()
    {
        if (!debugOverlay) return;

        int count;
        long ticks;
        string sender;
        lock (_lock)
        {
            count = _packetCount;
            ticks = _lastPacketTicks;
            sender = _lastSender;
        }

        string lastSeen = ticks == 0
            ? "never"
            : (DateTime.UtcNow - new DateTime(ticks, DateTimeKind.Utc)).TotalSeconds.ToString("0.00") + "s";

        GUI.Label(new Rect(10, 10, 600, 20), "UDP packets: " + count);
        GUI.Label(new Rect(10, 30, 600, 20), "Last packet: " + lastSeen + " ago");
        GUI.Label(new Rect(10, 50, 600, 20), "Last sender: " + (sender ?? "n/a"));
    }

    bool IsCalibrationPressed()
    {
#if ENABLE_INPUT_SYSTEM
        return Keyboard.current != null && Keyboard.current.spaceKey.wasPressedThisFrame;
#else
        return Input.GetKeyDown(KeyCode.Space);
#endif
    }

    void OnDestroy()
    {
        _running = false;
        _client?.Close();
        if (_thread != null && _thread.IsAlive)
        {
            _thread.Join(500);
        }
    }
}
