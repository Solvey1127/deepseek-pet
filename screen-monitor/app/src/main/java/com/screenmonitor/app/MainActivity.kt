package com.screenmonitor.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.screenmonitor.app.data.Permissions
import com.screenmonitor.app.ui.AppNav
import com.screenmonitor.app.ui.PermissionScreen
import com.screenmonitor.app.ui.theme.ScreenMonitorTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ScreenMonitorTheme {
                val lifecycleOwner = LocalLifecycleOwner.current
                var hasAccess by remember { mutableStateOf(Permissions.hasUsageAccess(this)) }

                // 每次回到前台重新检查权限（用户可能刚在系统设置里授权）
                androidx.compose.runtime.DisposableEffect(lifecycleOwner) {
                    val observer = LifecycleEventObserver { _, event ->
                        if (event == Lifecycle.Event.ON_RESUME) {
                            hasAccess = Permissions.hasUsageAccess(this@MainActivity)
                        }
                    }
                    lifecycleOwner.lifecycle.addObserver(observer)
                    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
                }

                if (hasAccess) {
                    AppNav()
                } else {
                    PermissionScreen(
                        onOpenSettings = { Permissions.openUsageAccessSettings(this@MainActivity) },
                        onRefresh = { hasAccess = Permissions.hasUsageAccess(this@MainActivity) }
                    )
                }
            }
        }
    }
}
