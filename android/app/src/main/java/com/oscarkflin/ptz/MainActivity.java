package com.oscarkflin.ptz;

import android.app.*;
import android.os.Bundle;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.content.res.ColorStateList;
import android.view.*;
import android.widget.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Touch-only Android test controller. No remote server required. */
public class MainActivity extends Activity {
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private SharedPreferences prefs;
    private EditText host, port;
    private TextView status;
    private Switch live;
    private LinearLayout root, presets;
    private volatile boolean armed = false;
    private int sequence = 0, speed = 6;
    private DatagramSocket socket;
    private JoystickView joystick;
    private SeekBar zoomSlider;
    private TextView motionLabel, zoomLabel;
    private float joystickX, joystickY;
    private long lastMoveTime;
    private String lastMotion = "";
    private int lastZoom = 0;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("controller", MODE_PRIVATE);
        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(22), dp(20), dp(32)); root.setBackgroundColor(Color.rgb(11,18,28));
        getWindow().setStatusBarColor(Color.rgb(11,18,28));
        getWindow().setNavigationBarColor(Color.rgb(11,18,28));
        scroll.addView(root); setContentView(scroll);
        label("◉  PTZ Controller", 28); label("YOUR CAMERA. AT YOUR FINGERTIPS.", 11);
        status = label("Demo mode · no commands sent", 14);
        host = field("Camera IPv4 address", prefs.getString("host", "192.168.1.120"));
        port = field("UDP port", prefs.getString("port", "52381"));
        live = new Switch(this); live.setText("Live camera control"); live.setPadding(0,dp(12),0,dp(12)); root.addView(live);
        live.setOnCheckedChangeListener((button, checked) -> {
            if (checked) {
                if (!validAddress()) { live.setChecked(false); return; }
                new AlertDialog.Builder(this).setTitle("Enable camera control?")
                    .setMessage("Commands will go to " + host.getText() + ":" + port.getText() + ". Start at low speed.")
                    .setPositiveButton("Enable", (d,w) -> { armed=true; host.setEnabled(false); port.setEnabled(false); saveAddress(); status.setText("Live · destination configured (camera not verified)"); })
                    .setNegativeButton("Cancel", (d,w) -> live.setChecked(false))
                    .setOnCancelListener(d -> live.setChecked(false)).show();
            } else { stop(); armed=false; host.setEnabled(true); port.setEnabled(true); }
        });
        label("Move the camera", 22);
        motionLabel=label("Drag gently for precise movement · release to stop",12);
        joystick=new JoystickView(this,this::analogMovement);
        root.addView(joystick,new LinearLayout.LayoutParams(-1,dp(265)));
        Button stopButton=button(root,"■   STOP ALL",()->{joystick.release();zoomSlider.setProgress(50);stop();});
        stopButton.setBackground(tint(Color.rgb(92,35,46)));stopButton.setTextColor(Color.rgb(255,192,199));
        label("Movement speed limit", 14);
        SeekBar slider = new SeekBar(this); slider.setMax(23); slider.setProgress(5); root.addView(slider);
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar s,int n,boolean user){speed=n+1;lastMotion="";analogMovement(joystickX,joystickY);}
            public void onStartTrackingTouch(SeekBar s){} public void onStopTrackingTouch(SeekBar s){}
        });
        label("Zoom",22);
        zoomLabel=label("Wide  −                 Release to stop                 +  Tele",12);
        zoomSlider=new SeekBar(this);zoomSlider.setMax(100);zoomSlider.setProgress(50);root.addView(zoomSlider);
        zoomSlider.setProgressTintList(ColorStateList.valueOf(Color.rgb(67,166,255)));
        zoomSlider.setThumbTintList(ColorStateList.valueOf(Color.rgb(112,192,255)));
        zoomSlider.setOnTouchListener((v,e)->{v.getParent().requestDisallowInterceptTouchEvent(true);if(e.getActionMasked()==MotionEvent.ACTION_CANCEL){zoomSlider.setProgress(50);zoomCommand(50);}return false;});
        zoomSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar s,int n,boolean user){if(user)zoomCommand(n);}
            public void onStartTrackingTouch(SeekBar s){}
            public void onStopTrackingTouch(SeekBar s){s.setProgress(50);zoomCommand(50);s.getParent().requestDisallowInterceptTouchEvent(false);}
        });
        label("Presets",20);
        label("Tap to recall · long press to rename, store or remove",13);
        presets = new LinearLayout(this); presets.setOrientation(LinearLayout.VERTICAL); root.addView(presets);
        if (!prefs.contains("initialized")) {
            String[] names={"Pulpit","Piano","Worship team","Wide stage","Audience"};
            SharedPreferences.Editor e=prefs.edit().putBoolean("initialized",true);
            for(int i=0;i<names.length;i++) e.putString("preset"+(i+1),names[i]); e.apply();
        }
        renderPresets(); button(root,"Add preset",()->editPreset(-1));
        label("No USB joystick support in this first Android build. Same Wi-Fi/LAN as camera required. No video preview.",13);
    }
    private TextView label(String text,int size){TextView t=new TextView(this);t.setText(text);t.setTextSize(size);t.setTextColor(Color.rgb(218,232,247));t.setPadding(0,10,0,10);root.addView(t);return t;}
    private EditText field(String hint,String value){EditText t=new EditText(this);t.setSingleLine(true);t.setHint(hint);t.setText(value);root.addView(t);return t;}
    private LinearLayout row(LinearLayout parent){LinearLayout r=new LinearLayout(this);r.setGravity(Gravity.CENTER);parent.addView(r);return r;}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private GradientDrawable tint(int color){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(14));d.setStroke(dp(1),Color.rgb(44,62,83));return d;}
    private Button button(LinearLayout parent,String text,Runnable action){Button b=new Button(this);b.setText(text);b.setAllCaps(false);b.setTextSize(15);b.setTextColor(Color.rgb(219,235,251));b.setBackground(tint(Color.rgb(24,39,57)));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(54));lp.setMargins(0,dp(5),0,dp(5));parent.addView(b,lp);b.setOnClickListener(v->action.run());return b;}
    private void analogMovement(float x,float y){
        joystickX=x;joystickY=y;
        float ax=Math.abs(x),ay=Math.abs(y);int pan=ax<.10f?0:x>0?1:-1,tilt=ay<.10f?0:y>0?1:-1;
        int ps=Math.max(1,Math.round((float)Math.pow(ax,1.6)*speed));
        int ts=Math.max(1,Math.round((float)Math.pow(ay,1.6)*Math.min(20,speed)));
        String intent=pan+":"+tilt+":"+ps+":"+ts;long now=android.os.SystemClock.uptimeMillis();
        if(!intent.equals(lastMotion)&&((pan==0&&tilt==0)||now-lastMoveTime>=50)){
            send(0x81,1,6,1,ps,ts,pan<0?1:pan>0?2:3,tilt<0?2:tilt>0?1:3,0xff);lastMotion=intent;lastMoveTime=now;
        }
        motionLabel.setText(pan==0&&tilt==0?"Centered · camera stopped":"Pan "+(pan==0?0:ps)+"  /  Tilt "+(tilt==0?0:ts)+" · release to stop");
    }
    private void zoomCommand(int progress){
        int delta=progress-50;int command=Math.abs(delta)<5?0:(delta>0?0x20:0x30)+Math.min(7,Math.round(Math.abs(delta)*7/50f));
        if(command!=lastZoom){send(0x81,1,4,7,command,0xff);lastZoom=command;}
        zoomLabel.setText(command==0?"Wide  −                 Centered · stopped                 +  Tele":(delta>0?"Zooming in":"Zooming out")+" · release to stop");
    }
    private void hold(LinearLayout parent,String text,int pan,int tilt,int zoom){
        Button b=button(parent,text,()->{});
        b.setOnTouchListener((v,event)->{
            if(event.getActionMasked()==MotionEvent.ACTION_DOWN){if(zoom!=0) send(0x81,1,4,7,zoom>0?0x24:0x34,0xff);else movement(pan,tilt);return true;}
            if(event.getActionMasked()==MotionEvent.ACTION_UP||event.getActionMasked()==MotionEvent.ACTION_CANCEL){stop();v.performClick();return true;}return true;
        });
    }
    private boolean validAddress(){
        try {String[] parts=host.getText().toString().trim().split("\\.");if(parts.length!=4)throw new Exception();for(String p:parts){int n=Integer.parseInt(p);if(n<0||n>255)throw new Exception();}int p=Integer.parseInt(port.getText().toString());if(p<1||p>65535)throw new Exception();return true;}
        catch(Exception e){status.setText("Enter a valid camera IPv4 address and port 1–65535");return false;}
    }
    private void saveAddress(){prefs.edit().putString("host",host.getText().toString().trim()).putString("port",port.getText().toString()).apply();}
    private void movement(int pan,int tilt){send(0x81,1,6,1,speed,Math.min(speed,20),pan<0?1:pan>0?2:3,tilt<0?2:tilt>0?1:3,0xff);}
    private void stop(){movement(0,0);send(0x81,1,4,7,0,0xff);}
    private void send(int... bytes){
        if(!armed){status.setText("Demo command · no network traffic");return;}
        final String address=host.getText().toString().trim(); final int destination=Integer.parseInt(port.getText().toString());
        network.execute(()->{try{
            if(socket==null)socket=new DatagramSocket();
            ByteBuffer packet=ByteBuffer.allocate(8+bytes.length);packet.putShort((short)0x0100).putShort((short)bytes.length).putInt(sequence++);
            for(int value:bytes)packet.put((byte)value);
            socket.send(new DatagramPacket(packet.array(),packet.capacity(),InetAddress.getByName(address),destination));
            runOnUiThread(()->status.setText("UDP command sent · camera response not verified"));
        }catch(Exception e){runOnUiThread(()->status.setText("Network error: "+e.getMessage()));}});
    }
    private void renderPresets(){
        presets.removeAllViews();
        for(int n=0;n<16;n++){final int number=n;String name=prefs.getString("preset"+n,null);if(name==null)continue;
            Button b=button(presets,n+" · "+name,()->send(0x81,1,4,0x3f,2,number,0xff));
            b.setOnLongClickListener(v->{new AlertDialog.Builder(this).setTitle("Preset "+number)
                .setItems(new String[]{"Rename label","Store current camera position","Remove local button"},(d,w)->{
                    if(w==0)editPreset(number);
                    if(w==1)new AlertDialog.Builder(this).setTitle("Overwrite camera preset "+number+"?").setMessage("Store the camera's current position in this slot?")
                        .setPositiveButton("Store",(a,c)->send(0x81,1,4,0x3f,1,number,0xff)).setNegativeButton("Cancel",null).show();
                    if(w==2)new AlertDialog.Builder(this).setTitle("Remove local button?").setMessage("The camera's stored position will remain.")
                        .setPositiveButton("Remove",(a,c)->{prefs.edit().remove("preset"+number).apply();renderPresets();}).setNegativeButton("Cancel",null).show();
                }).show();return true;});
        }
    }
    private void editPreset(int existing){
        LinearLayout form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(32,8,32,8);
        EditText number=new EditText(this);number.setHint("Camera slot 0–15");number.setInputType(2);if(existing>=0)number.setText(""+existing);number.setEnabled(existing<0);form.addView(number);
        EditText name=new EditText(this);name.setHint("Display name");if(existing>=0)name.setText(prefs.getString("preset"+existing,""));form.addView(name);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle(existing<0?"Add preset button":"Rename preset").setView(form).setPositiveButton("Save",null).setNegativeButton("Cancel",null).create();
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{try{
            int n=Integer.parseInt(number.getText().toString());String label=name.getText().toString().trim();
            if(n<0||n>15||label.isEmpty()||(existing<0&&prefs.contains("preset"+n)))throw new Exception();
            prefs.edit().putString("preset"+n,label).apply();renderPresets();dialog.dismiss();
        }catch(Exception e){name.setError("Use an unused slot 0–15 and a name");}}));dialog.show();
    }
    @Override protected void onPause(){if(joystick!=null)joystick.release();if(zoomSlider!=null){zoomSlider.setProgress(50);zoomCommand(50);}stop();armed=false;if(live!=null)live.setChecked(false);super.onPause();}
    @Override protected void onDestroy(){network.execute(()->{if(socket!=null)socket.close();});network.shutdown();super.onDestroy();}
}
