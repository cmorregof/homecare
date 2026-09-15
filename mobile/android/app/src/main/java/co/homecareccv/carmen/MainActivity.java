package co.homecareccv.carmen;

import android.os.Bundle;
import android.webkit.WebView;

import androidx.activity.OnBackPressedCallback;

import com.getcapacitor.BridgeActivity;

/**
 * Host activity for the CARMEN web app.
 *
 * The only thing added to the stock BridgeActivity is back navigation.
 * Capacitor 6.2.2 ships no back handling of its own — there is no canGoBack
 * call anywhere in @capacitor/android outside a Cordova mock — so the platform
 * default applies and the back gesture finishes the activity. In a shell around
 * a multi-page site that means leaving the patient dashboard, or the vitals
 * form half filled in, closes the app outright.
 *
 * Registering a callback on the dispatcher rather than overriding
 * onBackPressed() keeps this working on API 33+, where the old override is
 * deprecated and bypassed by predictive back.
 */
public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getOnBackPressedDispatcher()
            .addCallback(
                this,
                new OnBackPressedCallback(true) {
                    @Override
                    public void handleOnBackPressed() {
                        WebView webView = getBridge() == null ? null : getBridge().getWebView();
                        if (webView != null && webView.canGoBack()) {
                            webView.goBack();
                            return;
                        }
                        // Nothing left in history: stand down and let the
                        // platform close the app as it normally would.
                        setEnabled(false);
                        getOnBackPressedDispatcher().onBackPressed();
                    }
                }
            );
    }
}
