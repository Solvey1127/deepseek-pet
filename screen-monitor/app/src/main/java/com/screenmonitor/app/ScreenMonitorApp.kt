package com.screenmonitor.app

import android.app.Application
import com.screenmonitor.app.data.AppDatabase
import com.screenmonitor.app.data.UsageCollector
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class ScreenMonitorApp : Application() {

    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        instance = this
        // 应用启动时异步采集一次，保证打开就有数据
        applicationScope.launch {
            val dao = AppDatabase.get(this@ScreenMonitorApp).usageDao()
            UsageCollector.collect(this@ScreenMonitorApp, dao)
        }
    }

    companion object {
        lateinit var instance: ScreenMonitorApp
            private set
    }
}
